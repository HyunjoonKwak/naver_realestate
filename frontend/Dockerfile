FROM node:18-alpine

WORKDIR /app

# 패키지 파일 복사
COPY package*.json ./

# 모든 의존성 설치 (빌드에 필요)
RUN npm ci

# 애플리케이션 코드 복사
COPY . .

# Next.js 빌드
RUN npm run build

# 프로덕션 의존성만 재설치 (이미지 크기 최적화)
RUN npm prune --production

# 환경 변수 설정
ENV NODE_ENV=production
ENV PORT=3000

# 포트 노출
EXPOSE 3000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# 실행 명령
CMD ["npm", "start"]
