# 🚀 ParaPara 배포 가이드

## 📋 **현재 배포 상태**

### **프론트엔드 (Vercel)**
- ✅ 메인 URL: https://paraparavintage.vercel.app
- ✅ Preview URL: https://paraparavintage-pdu3c4ru7-aeongiings-projects.vercel.app
- ✅ Framework: Next.js 16.2.9
- ✅ Status: READY

### **백엔드 (EC2)**
- ⚠️ 현재 URL: http://100.53.237.32:8080
- ❌ **문제**: HTTP만 지원 (HTTPS 없음)
- ❌ **결과**: Mixed Content 차단 (Vercel HTTPS → 백엔드 HTTP 불가)

---

## 🔧 **필수 설정 작업**

### **1️⃣ Google OAuth 설정**

**Google Cloud Console 접속**: https://console.cloud.google.com/

1. **프로젝트 선택** (현재 사용 중인 프로젝트)
2. **API 및 서비스 → 사용자 인증 정보**
3. **OAuth 2.0 클라이언트 ID 편집**
4. **승인된 자바스크립트 원본에 추가**:
   ```
   https://paraparavintage.vercel.app
   https://paraparavintage-pdu3c4ru7-aeongiings-projects.vercel.app
   ```
5. **승인된 리디렉션 URI에 추가**:
   ```
   https://paraparavintage.vercel.app/api/auth/callback/google
   https://paraparavintage-pdu3c4ru7-aeongiings-projects.vercel.app/api/auth/callback/google
   ```

---

### **2️⃣ Vercel 환경변수 설정**

**Vercel 대시보드**: https://vercel.com/aeongiings-projects/paraparavintage

1. **Settings → Environment Variables**
2. **다음 변수 추가**:

#### **현재 (임시 - Mixed Content 차단됨)**
```
NEXT_PUBLIC_API_URL=http://100.53.237.32:8080
NEXT_PUBLIC_GOOGLE_CLIENT_ID=997464628687-ko00jm7bq33o8ips0obim7g4omjs2j3e.apps.googleusercontent.com
```

#### **HTTPS 설정 후 (권장)**
```
NEXT_PUBLIC_API_URL=https://api.paraparavintage.com
NEXT_PUBLIC_GOOGLE_CLIENT_ID=997464628687-ko00jm7bq33o8ips0obim7g4omjs2j3e.apps.googleusercontent.com
```

3. **Production, Preview, Development 모두 체크**
4. **Save**
5. **Deployments → Redeploy** (환경변수 적용)

---

## ⚠️ **CRITICAL: Mixed Content 문제**

### **문제**
```
Vercel (HTTPS) → Backend (HTTP)
    ❌ 브라우저가 보안상 차단!
```

브라우저 콘솔 에러:
```
Mixed Content: The page at 'https://paraparavintage.vercel.app' 
was loaded over HTTPS, but requested an insecure XMLHttpRequest endpoint 
'http://100.53.237.32:8080'. This request has been blocked.
```

### **해결 방법**

---

## 🔐 **백엔드 HTTPS 설정 (필수)**

### **방법 1: Nginx + Let's Encrypt (권장)**

#### **1단계: 도메인 연결**
```bash
# DNS 설정 (예: Cloudflare, Route53)
api.paraparavintage.com → A Record → 100.53.237.32
```

#### **2단계: SSH 접속 후 Nginx 설치**
```bash
ssh user@100.53.237.32

# Nginx 설치
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx -y

# Nginx 설정 생성
sudo nano /etc/nginx/sites-available/parapara-api
```

#### **3단계: Nginx 설정 파일**
```nginx
server {
    listen 80;
    server_name api.paraparavintage.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/parapara-api /etc/nginx/sites-enabled/

# Nginx 테스트 & 재시작
sudo nginx -t
sudo systemctl restart nginx
```

#### **4단계: SSL 인증서 발급 (Let's Encrypt)**
```bash
sudo certbot --nginx -d api.paraparavintage.com
```

**질문에 답변**:
- Email: (관리자 이메일 입력)
- Terms: A (동의)
- Redirect: 2 (HTTP → HTTPS 자동 리다이렉트)

#### **5단계: 자동 갱신 설정**
```bash
# 자동 갱신 테스트
sudo certbot renew --dry-run

# Cron 설정 (자동)
sudo systemctl status certbot.timer
```

---

### **방법 2: Cloudflare Tunnel (간단)**

#### **1단계: Cloudflared 설치**
```bash
ssh user@100.53.237.32

# Cloudflared 설치
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

#### **2단계: 터널 생성**
```bash
cloudflared tunnel login
cloudflared tunnel create parapara-api
cloudflared tunnel route dns parapara-api api.paraparavintage.com
```

#### **3단계: 설정 파일**
```yaml
# ~/.cloudflared/config.yml
tunnel: <TUNNEL-ID>
credentials-file: /root/.cloudflared/<TUNNEL-ID>.json

ingress:
  - hostname: api.paraparavintage.com
    service: http://localhost:8080
  - service: http_status:404
```

#### **4단계: 터널 실행**
```bash
cloudflared tunnel run parapara-api

# 백그라운드 실행 (systemd)
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

---

### **방법 3: Render로 백엔드 이전 (가장 간단)**

#### **render.yaml 이미 준비됨!**

1. **Render 대시보드**: https://dashboard.render.com/
2. **New → Blueprint**
3. **GitHub 저장소 연결**: `aeongiing/Primero`
4. **자동 배포 시작**
5. **Render가 제공하는 HTTPS URL**:
   ```
   https://parapara-api-XXXX.onrender.com
   ```

6. **Vercel 환경변수 업데이트**:
   ```
   NEXT_PUBLIC_API_URL=https://parapara-api-XXXX.onrender.com
   ```

---

## 📝 **백엔드 CORS 설정 확인**

`backend/app/main.py`에서 Vercel URL 추가 확인:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://paraparavintage.vercel.app",
        "https://paraparavintage-pdu3c4ru7-aeongiings-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**수정 후 push & 서버 재배포!**

---

## ✅ **배포 완료 체크리스트**

### **프론트엔드 (Vercel)**
- [ ] Google OAuth 원본 URL 추가
- [ ] Vercel 환경변수 설정
- [ ] Redeploy 실행

### **백엔드 (HTTPS 필수)**
- [ ] 방법 선택 (Nginx / Cloudflare / Render)
- [ ] HTTPS 설정 완료
- [ ] CORS 설정 업데이트
- [ ] Health check: `https://api.paraparavintage.com/health`
- [ ] API 문서: `https://api.paraparavintage.com/docs`

### **최종 확인**
- [ ] 프론트엔드 접속: https://paraparavintage.vercel.app
- [ ] Google 로그인 테스트
- [ ] 브라우저 콘솔 에러 없음 확인
- [ ] 회원가입 성공 확인

---

## 🎯 **권장 순서**

### **빠른 해결 (15분)**
1. Render에 백엔드 배포
2. Render HTTPS URL 받기
3. Vercel 환경변수 업데이트
4. Google OAuth 설정
5. 테스트

### **프로덕션 구성 (1시간)**
1. 도메인 구입 (api.paraparavintage.com)
2. Nginx + Let's Encrypt 설정
3. Vercel 환경변수 업데이트
4. Google OAuth 설정
5. 모니터링 설정

---

## 📞 **팀원 공유사항**

### **백엔드 담당자에게**
```
현재 백엔드 HTTP 때문에 프론트엔드에서 Mixed Content 차단됩니다.

해결 방법:
1. Nginx + Let's Encrypt로 HTTPS 설정
2. 또는 Render로 이전 (render.yaml 준비됨)

EC2 IP: 100.53.237.32
필요 작업: HTTPS 인증서 설치
```

### **프론트엔드 담당자에게**
```
Vercel 배포 완료!
URL: https://paraparavintage.vercel.app

필요 작업:
1. Vercel 환경변수 설정
2. Google OAuth 승인 URL 추가

백엔드 HTTPS 완료되면 바로 동작합니다!
```

---

## 🔗 **유용한 링크**

- **프론트**: https://paraparavintage.vercel.app
- **백엔드 (현재)**: http://100.53.237.32:8080
- **Google Console**: https://console.cloud.google.com/
- **Vercel Dashboard**: https://vercel.com/aeongiings-projects/paraparavintage
- **GitHub**: https://github.com/aeongiing/Primero
