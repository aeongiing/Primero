# Requirements Document

## Introduction

Primero is a secondhand clothing multi-platform listing automation service built for a netzero hackathon. A seller photographs a single garment once, and Primero automatically classifies it, generates a polished product description, produces clean thumbnails, and publishes the listing across multiple resale marketplaces (번개장터/bunjang, fruits, 차란/charan, 당근/karrot, and eBay). When the item sells on any one platform, Primero removes the listing from every other platform and marks the product sold. Unsold items are automatically discounted over time to keep inventory circulating, reducing textile waste in support of the netzero goal.

The system is composed of a FastAPI + async SQLAlchemy backend on AWS, a Next.js frontend, an AI/media pipeline (AWS Rekognition, Bedrock Claude, rembg/U^2-Net, Pillow) running on ECS Fargate, and an automation/infrastructure layer (Google OAuth + JWT, OpenClaw automation engine, SQS workers, EventBridge/Lambda schedulers, and a Fargate poller). Work is divided between two scopes: the AI/media pipeline (Backend A) and automation + infrastructure (Backend B).

This document defines requirements for both scopes. The Product record is treated as the single source of truth (SSOT): every platform listing is derived from it, and all state changes (price, sale, discount) propagate from the Product to the platforms. Partial failures are isolated so that one platform's failure does not block work on other platforms. Authentication, infrastructure provisioning details, and frontend UI rendering are referenced where they intersect with backend behavior but are otherwise out of scope.

## Glossary

- **Primero**: The overall multi-platform listing automation service described in this document.
- **Listing_API**: The FastAPI application that exposes REST endpoints and orchestrates the system.
- **AI_Worker**: The ECS Fargate worker process that runs classification, description generation, and thumbnail processing.
- **Media_Service**: The component responsible for image upload, S3 storage, and thumbnail processing requests.
- **S3_Store**: The AWS S3 bucket that stores product images and processed thumbnails.
- **Classifier**: The component that auto-classifies clothing category and color using AWS Rekognition and the K-Fashion model.
- **Description_Generator**: The component that generates product descriptions using the AWS Bedrock Claude API.
- **Thumbnail_Processor**: The component that removes image backgrounds (rembg/U^2-Net) and enhances images (Pillow).
- **Auth_Service**: The component that performs Google OAuth authentication and issues Primero JWTs.
- **JWT**: A JSON Web Token issued by the Auth_Service that authenticates a User to the Listing_API.
- **Platform_Adapter**: A pluggable component implementing a common interface for one external marketplace.
- **Adapter_Registry**: The registry that maps a platform identifier to its Platform_Adapter.
- **OpenClaw_Engine**: The browser-automation engine used by Platform_Adapters to register and manage listings on platforms without an official API.
- **Publish_Worker**: The worker process that consumes SQS publish tasks and invokes Platform_Adapters.
- **Task_Queue**: The AWS SQS queue carrying listing publish tasks.
- **Sale_Poller**: The Fargate worker that polls platforms for sale completion.
- **Discount_Scheduler**: The EventBridge-triggered AWS Lambda that applies automatic discounts to unsold products.
- **Secrets_Store**: AWS Secrets Manager, which stores platform credentials referenced by `credential_key`.
- **User**: An authenticated seller account (User model: id, email, google_id).
- **Product**: A garment record (Product model) with status in {draft, listing, listed, sold, unlisted} and fields title, brand, description, category, condition (1-10), price, size, chest, total_length, waist, hip, rise.
- **Product_Image**: An uploaded image record (ProductImage model) with fields s3_key and order.
- **Platform_Account**: A User's credential binding to one marketplace (PlatformAccount model: platform, credential_key, is_active).
- **Listing**: A published instance of a Product on one platform (Listing model) with status in {pending, active, sold, removed}.
- **Sale**: A record (Sale model) capturing the product, listing, platform, and sold_at timestamp of a completed sale.
- **AI_Analysis_Result**: The structured output of AI analysis (AIAnalysisResult schema: title, brand, category, description, condition, size, chest, total_length, waist, hip, rise, colors, material).
- **Supported_Platform**: One of bunjang, fruits, charan, karrot, or ebay.
- **Image_Order**: The integer position of a Product_Image, where 0=front, 1=zoom, 2=back, 3=detail, 4=stain, 5=tag.
- **Mapping_Engine**: The component that maps a Product's canonical fields to one platform's required field and category schema using declarative mapping configuration.
- **Canonical_Value_Set**: The reference set of field values adopted from the 차란/charan platform, from which values for other platforms are reduced or mapped.
- **Condition_Grade**: A platform-specific condition label (for example Excellent, Great, Very-good, Good) derived from a Product's numeric condition.
- **unmapped_fields**: The collection of canonical field values that could not be mapped to a target platform's allowed values and require manual selection.
- **missing_required**: The collection of a target platform's required fields that remain empty after mapping.
- **Error_Response**: The common error payload of the form `{ "error_code": <string>, "message": <string>, "details": <object> }`.

## Requirements

### Requirement 1: Photo Upload and S3 Storage

**User Story:** As a seller, I want to upload garment photos that are stored reliably, so that my product has images to analyze and publish.

#### Acceptance Criteria

1. WHEN an authenticated User uploads an image for a Product that belongs to that User, THE Media_Service SHALL store the image in the S3_Store using the key format `{user_id}/{product_id}/{order}.jpg`.
2. THE Media_Service SHALL accept an Image_Order value as an integer in the range 0 to 5 inclusive, mapping 0 to front, 1 to zoom, 2 to back, 3 to detail, 4 to stain, and 5 to tag.
3. WHEN an image is stored in the S3_Store, THE Media_Service SHALL create exactly one Product_Image record containing the s3_key and the Image_Order, and SHALL return a success response containing the s3_key and the Image_Order.
4. THE Media_Service SHALL store at most 6 Product_Image records per Product, with at most one Product_Image per distinct Image_Order value.
5. IF a User uploads an image with an Image_Order that has no existing Product_Image and the Product already has 6 stored Product_Image records, THEN THE Media_Service SHALL reject the upload, SHALL NOT store the image or create a Product_Image record, and SHALL return an error response indicating the per-product image limit of 6.
6. IF a User uploads an image with an Image_Order outside the integer range 0 to 5 inclusive, THEN THE Media_Service SHALL reject the upload, SHALL NOT store the image or create a Product_Image record, and SHALL return a validation error.
7. WHEN a User uploads an image with an Image_Order that already has a stored Product_Image for that Product, THE Media_Service SHALL overwrite the stored image at that Image_Order and SHALL keep exactly one Product_Image record for that Image_Order.
8. IF an upload references a product_id that does not belong to the authenticated User, THEN THE Media_Service SHALL reject the upload, SHALL NOT store the image or create a Product_Image record, and SHALL return an authorization error.
9. IF a User uploads a file whose type is neither JPEG nor PNG, or whose size exceeds 10 megabytes, THEN THE Media_Service SHALL reject the upload, SHALL NOT store the image or create a Product_Image record, and SHALL return a validation error.
10. IF storing the image in the S3_Store fails, THEN THE Media_Service SHALL NOT create a Product_Image record and SHALL return an error response indicating the storage failure.

### Requirement 2: Clothing Category and Color Classification

**User Story:** As a seller, I want my garment's category and colors detected automatically, so that I do not have to enter them manually.

#### Acceptance Criteria

1. WHEN AI analysis is requested for a Product that has at least one Product_Image, THE Classifier SHALL produce a clothing category and a list of colors using AWS Rekognition and the K-Fashion model.
2. THE Classifier SHALL return the category as a non-empty string and SHALL return colors as a list containing between 1 and 5 color values inclusive.
3. THE Classifier SHALL return every color value as a member of the charan 대표 색상 set: 블랙, 차콜, 레드, 화이트, 그레이, 네이비, 아이보리, 베이지, 카키, 민트, 그린, 블루, 스카이블루, 퍼플, 라벤더, 와인, 핑크, 옐로우, 오렌지, 브라운.
4. IF the Classifier cannot determine a category with a confidence at or above the configured category confidence threshold, which is a value in the range 0.0 to 1.0 inclusive with a default of 0.50, THEN THE Classifier SHALL return the category value "unknown".
5. IF no color reaches the configured color confidence threshold, THEN THE Classifier SHALL return the single highest-confidence color from the charan 대표 색상 set, so that the colors list always contains at least one member.
6. IF a Product has no Product_Image when AI analysis is requested, THEN THE Listing_API SHALL reject the request, SHALL NOT invoke the Classifier, SHALL leave the Product unchanged, and SHALL return an error indicating that at least one image is required.
7. IF AWS Rekognition returns an error or does not respond within the configured classification timeout, which is a value in the range 1 to 60 seconds inclusive with a default of 30 seconds, THEN THE Classifier SHALL return an error result that identifies the classification step as the failing step and SHALL NOT persist any partial classification values.

### Requirement 3: Product Description Auto-Generation

**User Story:** As a seller, I want a complete product listing draft generated from my photos, so that I can publish quickly without writing copy.

#### Acceptance Criteria

1. WHEN AI analysis is requested for a Product, THE Description_Generator SHALL produce an AI_Analysis_Result using the AWS Bedrock Claude API, completing the Bedrock call within 30 seconds.
2. THE Description_Generator SHALL populate the title, brand, category, description, condition, colors, and material fields of the AI_Analysis_Result as non-null and non-empty values.
3. THE Description_Generator SHALL produce a condition value in the integer range 1 to 10 inclusive.
4. THE Description_Generator SHALL return colors as a list containing between 1 and 4 color values inclusive.
5. WHERE the garment type has applicable measurements, THE Description_Generator SHALL populate the corresponding size, chest, total_length, waist, hip, and rise measurement fields as integers in the range 1 to 500 centimeters inclusive, and SHALL set non-applicable measurement fields to null.
6. THE Description_Generator SHALL produce a title with a length in the range 1 to 200 characters inclusive and a description with a length in the range 1 to 2000 characters inclusive.
7. WHEN AI analysis completes successfully, THE Listing_API SHALL return the AI_Analysis_Result via the `POST /products/analyze` endpoint.
8. IF the AWS Bedrock Claude API returns an error or does not respond within 30 seconds, THEN THE Description_Generator SHALL return an error result that identifies the description step as the failing step, excludes any secret value, and leaves the Product unchanged.

### Requirement 4: Thumbnail Background Removal and Enhancement

**User Story:** As a seller, I want clean, enhanced thumbnails generated from my photos, so that my listings look professional across platforms.

#### Acceptance Criteria

1. WHEN thumbnail processing is requested for a Product_Image, THE Thumbnail_Processor SHALL remove the image background using rembg/U^2-Net, producing an intermediate image in which background pixels are made transparent.
2. WHEN background removal completes successfully, THE Thumbnail_Processor SHALL enhance the result using Pillow by resizing it to a square output of 1000 x 1000 pixels with the subject preserved at its original aspect ratio and centered on a uniform background.
3. IF thumbnail processing for a single Product_Image does not complete within 30 seconds, THEN THE Thumbnail_Processor SHALL abort the operation, leave any existing thumbnail unchanged, and return an error indicating a processing timeout for the affected image key.
4. WHEN thumbnail processing completes, THE Thumbnail_Processor SHALL store the processed thumbnail in the S3_Store and associate the stored thumbnail key with the originating Product_Image.
5. THE AI_Worker SHALL execute classification, description generation, and thumbnail processing on ECS Fargate.
6. IF the source Product_Image cannot be retrieved from the S3_Store, THEN THE Thumbnail_Processor SHALL return an error identifying the missing image key and SHALL not create or overwrite any thumbnail for that image.
7. IF background removal fails for a Product_Image, THEN THE Thumbnail_Processor SHALL store the enhanced original image, resized to a square output of 1000 x 1000 pixels, as the thumbnail and SHALL record a status indicating that background removal did not succeed.

### Requirement 5: Google OAuth Authentication and JWT Issuance

**User Story:** As a seller, I want to sign in with my Google account, so that I can access my products securely.

#### Acceptance Criteria

1. WHEN a User completes Google OAuth with a Google id_token that is successfully verified, THE Auth_Service SHALL issue a Primero JWT that identifies the User by the User's unique identifier and that expires 60 minutes after issuance.
2. WHEN a User completes Google OAuth successfully and no User record exists for the returned google_id, THE Auth_Service SHALL create exactly one User record storing the returned email and google_id, and THE Auth_Service SHALL issue a JWT for that User.
3. WHEN a User completes Google OAuth successfully and a User record already exists for the returned google_id, THE Auth_Service SHALL issue a JWT for the existing User and SHALL NOT create an additional User record.
4. IF a User completes Google OAuth successfully and the returned email already belongs to a User record with a different google_id, THEN THE Auth_Service SHALL reject the request, SHALL return an authentication error indicating the email is already associated with another account, and SHALL NOT create or modify any User record.
5. WHEN a request is made to the `GET /me` endpoint with a JWT that is present, well-formed, and unexpired, THE Listing_API SHALL return the authenticated User's profile containing the User's identifier, email, and account creation timestamp.
6. IF a request to a protected endpoint includes a JWT that is missing, malformed, or expired, THEN THE Listing_API SHALL reject the request without performing the requested operation and SHALL return an unauthorized error response indicating that valid authentication is required.
7. IF Google OAuth fails, is denied by the User, or the returned id_token cannot be verified, THEN THE Auth_Service SHALL return an authentication error indicating the login was not successful, SHALL NOT issue a JWT, and SHALL NOT create or modify any User record.

### Requirement 6: Platform Account Registration

**User Story:** As a seller, I want to connect my marketplace accounts, so that Primero can publish on my behalf.

#### Acceptance Criteria

1. WHEN a User registers a Platform_Account, THE Listing_API SHALL store the platform identifier, of at most 50 characters, and a credential_key, of at most 500 characters, that references the Secrets_Store.
2. THE Listing_API SHALL treat a platform identifier as valid only when it is a case-sensitive exact match of one Supported_Platform identifier in the set: bunjang, fruits, charan, karrot, ebay.
3. WHEN a Platform_Account is registered with a valid platform identifier and credentials, THE Listing_API SHALL store the User's platform credentials in the Secrets_Store and SHALL persist only the credential_key reference in the Platform_Account record.
4. WHEN a Platform_Account is created, THE Listing_API SHALL set is_active to true by default.
5. THE Listing_API SHALL exclude every plaintext credential value from the Platform_Account record, from log entries, and from error responses, referencing credentials by credential_key name only.
6. IF a User registers a platform identifier that is not a case-sensitive exact match of a Supported_Platform identifier, THEN THE Listing_API SHALL reject the request, SHALL NOT persist a Platform_Account record, SHALL NOT store any credentials in the Secrets_Store, and SHALL return a validation error.
7. IF a User registers a Platform_Account with a missing or empty platform identifier or missing or empty credentials, THEN THE Listing_API SHALL reject the request, SHALL NOT persist a Platform_Account record, and SHALL return a validation error naming the missing field.
8. IF a User registers a Platform_Account for a platform identifier for which that User already has a Platform_Account with is_active value true, THEN THE Listing_API SHALL reject the request, SHALL leave the existing Platform_Account record unchanged, and SHALL return a duplicate-account error.

### Requirement 7: Platform Adapter Registry

**User Story:** As a developer, I want platform integrations behind a common adapter interface, so that platforms can be added or swapped without changing core logic.

#### Acceptance Criteria

1. THE Adapter_Registry SHALL map each Supported_Platform identifier (bunjang, fruits, charan, karrot, ebay) to exactly one Platform_Adapter.
2. WHEN the Listing_API requests a Platform_Adapter for a registered Supported_Platform, THE Adapter_Registry SHALL return the Platform_Adapter for that platform within 100 milliseconds.
3. THE Adapter_Registry SHALL provide each Platform_Adapter through a common interface that supports exactly three operations: publishing a listing, removing a listing, and querying sale status.
4. WHERE a Supported_Platform provides an official API, THE Platform_Adapter for that platform MAY use the official API instead of the OpenClaw_Engine.
5. WHERE a Supported_Platform does not provide an official API, THE Platform_Adapter SHALL use the OpenClaw_Engine to register and manage listings.
6. IF a Platform_Adapter is requested for a platform identifier that is not registered, THEN THE Adapter_Registry SHALL return an error identifying the unregistered platform identifier, SHALL return no adapter, and SHALL exclude any credential value from the error.
7. IF a Platform_Adapter registration would map a Supported_Platform identifier that is already registered, THEN THE Adapter_Registry SHALL reject the duplicate registration so that each identifier maps to exactly one Platform_Adapter.
8. THE Adapter_Registry SHALL isolate each Platform_Adapter so that a failure in one Platform_Adapter does not prevent retrieval or operation of other Platform_Adapters.

### Requirement 8: Platform Field and Category Mapping

**User Story:** As a seller, I want my single product converted into each platform's required fields and categories automatically, so that listings are valid on every marketplace without manual re-entry.

#### Acceptance Criteria

1. WHEN a Product is prepared for publication to a Supported_Platform, THE Mapping_Engine SHALL map the Product's canonical fields to that platform's required fields and category using declarative mapping configuration, producing identical output for identical Product input and mapping configuration.
2. THE Mapping_Engine SHALL derive the Condition_Grade from the Product condition score using mutually exclusive and contiguous thresholds: a score in the range 9.0 to 10.0 inclusive maps to Excellent, a score of 8.0 or greater and below 9.0 maps to Great, a score of 6.5 or greater and below 8.0 maps to Very-good, and a score of 0.0 or greater and below 6.5 maps to Good.
3. WHERE a Supported_Platform provides no condition grade field, specifically 번개장터/bunjang and 당근/karrot, THE Mapping_Engine SHALL include the condition information within the listing description body.
4. WHERE a target platform field constrains the maximum number of selectable values, such as the 차란/charan 계절 and 소재 fields whose maximum is 4 values, THE Mapping_Engine SHALL order the candidate values by their rank in the declarative mapping configuration, break ties by the order of values in the Canonical_Value_Set, and truncate the ordered selection to the platform's maximum count.
5. IF a canonical field value cannot be mapped to a target platform's allowed value, THEN THE Mapping_Engine SHALL add that value to unmapped_fields and SHALL request manual selection.
6. IF a target platform's required field remains empty after mapping, THEN THE Mapping_Engine SHALL include that field in missing_required and SHALL withhold the listing from registration.
7. THE Mapping_Engine SHALL always return unmapped_fields and missing_required collections in its mapping result, including when both collections are empty.
8. THE Mapping_Engine SHALL adopt the Canonical_Value_Set from the 차란/charan platform as the canonical reference and SHALL reduce or map those values for other Supported_Platforms.
9. IF a Product's condition score is missing, non-numeric, or outside the range 0.0 to 10.0 inclusive, THEN THE Mapping_Engine SHALL withhold the listing from registration and SHALL return an error that identifies the invalid condition score and excludes any secret value.

### Requirement 9: Listing Publication via SQS

**User Story:** As a seller, I want my product published to my connected platforms automatically, so that I reach more buyers without manual posting.

#### Acceptance Criteria

1. WHEN a User requests publication of a Product, THE Listing_API SHALL enqueue one publish task per Platform_Account whose is_active value is true onto the Task_Queue.
2. WHEN publication is requested for a Product, THE Listing_API SHALL set the Product status to listing.
3. WHEN a publish task is enqueued for a platform, THE Listing_API SHALL create a Listing record with status pending for that Product and Platform_Account.
4. IF the Mapping_Engine returns a non-empty missing_required collection for a platform, THEN THE Publish_Worker SHALL withhold registration on that platform, SHALL leave the corresponding Listing in status pending, and SHALL record the names of the missing_required fields on that Listing.
5. WHEN the Publish_Worker consumes a publish task and the Platform_Adapter registers the listing successfully, THE Publish_Worker SHALL set the corresponding Listing status to active and store the returned platform_product_id.
6. WHEN all Listing records for a Product reach status active, THE Listing_API SHALL set the Product status to listed.
7. IF the Platform_Adapter fails to register a listing for a publish task, THEN THE Publish_Worker SHALL retry up to a maximum of 3 attempts, and upon exhausting the 3 attempts SHALL set the corresponding Listing status to removed and SHALL record the failure reason without including any secret value.
8. THE Publish_Worker SHALL process each platform's publish task independently so that a failure on one platform does not prevent registration on other platforms.
9. THE Listing_API SHALL enqueue publish tasks only for Platform_Accounts whose is_active value is true.
10. IF a User requests publication of a Product for which no Platform_Account has is_active value true, THEN THE Listing_API SHALL reject the request, SHALL NOT enqueue any publish task, and SHALL return an error indicating that no active platform account exists.
11. WHEN a request is made to `GET /listings/{product_id}` for a Product belonging to the authenticated User, THE Listing_API SHALL return the Listing records and their statuses for that Product.
12. IF a request to `GET /listings/{product_id}` references a Product that does not belong to the authenticated User, THEN THE Listing_API SHALL reject the request and return an authorization error.

### Requirement 10: Sale Completion Synchronization

**User Story:** As a seller, I want all my listings removed automatically when an item sells anywhere, so that I never sell the same garment twice.

#### Acceptance Criteria

1. WHILE a Product has at least one Listing with status active, THE Sale_Poller SHALL poll each active Listing's platform for sale completion at a configured interval of 60 seconds.
2. WHEN a platform reports that a Listing is sold, THE Listing_API SHALL set that Listing status to sold and SHALL create exactly one Sale record capturing the product, listing, platform, and sold_at timestamp.
3. IF a Sale record already exists for the Product when a platform reports a Listing as sold, THEN THE Listing_API SHALL NOT create a second Sale record and SHALL leave the existing Product and Sale records unchanged.
4. WHEN a Listing is marked sold, THE Listing_API SHALL request removal of every other Listing for the same Product whose status is active through the corresponding Platform_Adapters.
5. WHEN every other active Listing for a Product has been successfully removed following a sale, THE Listing_API SHALL set those Listing statuses to removed.
6. WHEN a sale is recorded for a Product, THE Listing_API SHALL set the Product status to sold.
7. WHEN a request is made to `POST /listings/{listing_id}/sold`, THE Listing_API SHALL mark the Listing sold and SHALL trigger the same removal and status updates as defined in criteria 2 through 6.
8. IF removal of another Listing fails during sale synchronization, THEN THE Listing_API SHALL retry that removal up to a configured maximum of 3 attempts, and IF all attempts fail, THEN THE Listing_API SHALL leave that Listing status as active and SHALL record the failure with the affected Listing identifier and a failure reason that excludes secret values.
9. WHILE a Product status is sold, THE Sale_Poller SHALL NOT poll that Product's Listings.

### Requirement 11: Automatic Discount of Unsold Products

**User Story:** As a seller, I want unsold items discounted automatically over time, so that they sell faster and stay out of the landfill.

#### Acceptance Criteria

1. WHILE a Product status is listed and the Product has remained unsold for 7 or more days since its most recent price change, THE Discount_Scheduler SHALL reduce the Product price by 10 percent of its current price.
2. WHEN the Discount_Scheduler reduces a Product price, THE Discount_Scheduler SHALL round the resulting price to the nearest integer, rounding halves upward to the next integer.
3. IF a 10 percent reduction would produce a rounded price below the minimum price floor of 1 currency unit, THEN THE Discount_Scheduler SHALL leave the Product price unchanged and SHALL NOT mark a price change for that Product.
4. WHEN a Product price is reduced, THE Discount_Scheduler SHALL propagate the updated price to every active Listing for that Product through the corresponding Platform_Adapters.
5. THE Discount_Scheduler SHALL be triggered by AWS EventBridge on a recurring schedule of once every 24 hours.
6. WHEN a Product price is reduced, THE Discount_Scheduler SHALL record the price change with a timestamp so that the next discount is evaluated relative to the new price and no earlier than 7 days after this change.
7. WHILE a Product has already had a price reduction recorded within the preceding 7 days, THE Discount_Scheduler SHALL NOT apply a further reduction to that Product.
8. IF propagation of a reduced price to a Listing fails, THEN THE Discount_Scheduler SHALL retry the propagation up to 3 total attempts and SHALL record each Listing that could not be updated together with the failure reason, without blocking propagation to other Listings.
9. THE Discount_Scheduler SHALL apply discounts only to Products whose status is listed.

### Requirement 12: Credential Confidentiality

**User Story:** As a seller, I want my platform credentials kept secret, so that my marketplace accounts are never exposed.

#### Acceptance Criteria

1. WHEN the Listing_API or any worker needs a platform credential or external API key, THE component SHALL load the value only from the Secrets_Store, referenced by its credential_key, and SHALL NOT read it from source files, environment-committed files, or the database.
2. WHEN the Listing_API persists a Platform_Account record, THE Listing_API SHALL store only the credential_key reference and SHALL exclude every plaintext credential value, such that a field-by-field inspection of the persisted record contains no credential value.
3. WHEN the Listing_API or any worker writes a log entry or constructs an Error_Response, THE component SHALL reference credentials and API keys by credential_key name only and SHALL exclude every credential and key value, such that no full or partial credential value appears in the emitted text.
4. IF a component must report a credential-related failure, THEN THE component SHALL return an Error_Response that identifies the credential by credential_key name, excludes the credential value, and indicates the failure cause without exposing the value.
5. IF the Secrets_Store is unavailable or does not return a requested credential_key within 5 seconds, THEN THE component SHALL abort the dependent operation, SHALL NOT fall back to any plaintext or cached source, and SHALL return an Error_Response identifying the affected credential_key name without the credential value.

### Requirement 13: Common Error Response Format

**User Story:** As a frontend developer, I want all backend errors returned in one consistent shape, so that the client can handle failures uniformly.

#### Acceptance Criteria

1. IF a request to the Listing_API fails for any reason, THEN THE Listing_API SHALL return an Error_Response containing exactly three fields named error_code, message, and details, with no fields omitted.
2. THE Listing_API SHALL set the Error_Response error_code field to a non-empty string of 1 to 64 characters drawn from a predefined set of error codes that includes "VALIDATION_ERROR".
3. THE Listing_API SHALL set the Error_Response message field to a human-readable string of 1 to 500 characters that describes the failure and excludes any secret value, including API keys and platform credentials, referencing secrets by name only.
4. WHEN a request fails input validation, THE Listing_API SHALL return an Error_Response with error_code set to "VALIDATION_ERROR".
5. THE Listing_API SHALL return the Error_Response details field as an object, returning an empty object when no additional detail is available.
6. IF a request fails after partial state changes, THEN THE Listing_API SHALL preserve the Canonical Product in its pre-request state and indicate the failure through the Error_Response.
