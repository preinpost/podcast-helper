# Kubernetes 배포 가이드

이 문서는 Podcast Helper Bot을 Kubernetes 클러스터에 배포하는 방법을 설명합니다.

## 사전 준비사항

- Kubernetes 클러스터 접근 권한
- `kubectl` 설치 및 설정
- Docker 설치 (이미지 빌드용)
- Container Registry 접근 권한 (Docker Hub, GCR, ECR 등)
- Telegram Bot Token
- OpenAI API Key

## 1. Docker 이미지 빌드

```bash
# 이미지 빌드
docker build -t podcast-helper:latest .

# 본인의 레지스트리로 태그 (예시)
docker tag podcast-helper:latest your-registry.com/podcast-helper:latest
# 또는 Docker Hub 사용 시
docker tag podcast-helper:latest your-dockerhub-username/podcast-helper:latest
```

## 2. 이미지 레지스트리에 푸시

```bash
# Docker Hub 로그인 (필요시)
docker login

# 이미지 푸시
docker push your-registry.com/podcast-helper:latest
# 또는
docker push your-dockerhub-username/podcast-helper:latest
```

## 3. Kubernetes Secret 생성

### 방법 1: kubectl 명령어 사용 (권장)

```bash
kubectl create secret generic podcast-helper-secrets \
  --from-literal=telegram-bot-token='YOUR_TELEGRAM_BOT_TOKEN' \
  --from-literal=openai-api-key='YOUR_OPENAI_API_KEY' \
  --from-literal=allowed-user-ids='USER_ID_1,USER_ID_2'
```

### 방법 2: YAML 파일 사용

```bash
# secret.example.yaml을 복사
cp k8s/secret.example.yaml k8s/secret.yaml

# secret.yaml 편집하여 실제 값 입력 (base64 인코딩 필요)
# Base64 인코딩: echo -n 'YOUR_VALUE' | base64

# Secret 생성
kubectl apply -f k8s/secret.yaml
```

**주의**: `k8s/secret.yaml`은 민감한 정보를 포함하므로 Git에 커밋하지 마세요!

## 4. Deployment 설정 수정

`k8s/deployment.yaml` 파일에서 이미지 경로를 수정하세요:

```yaml
image: your-registry.com/podcast-helper:latest
```

## 5. Deployment 배포

```bash
# Deployment 생성
kubectl apply -f k8s/deployment.yaml

# 배포 상태 확인
kubectl get deployments
kubectl get pods
```

## 6. 로그 확인

```bash
# Pod 이름 확인
kubectl get pods

# 로그 확인
kubectl logs -f <pod-name>

# 실시간 로그 스트림
kubectl logs -f deployment/podcast-helper-bot
```

## 7. 업데이트 배포

```bash
# 새 이미지 빌드 및 푸시
docker build -t your-registry.com/podcast-helper:v1.1.0 .
docker push your-registry.com/podcast-helper:v1.1.0

# Deployment 업데이트
kubectl set image deployment/podcast-helper-bot \
  bot=your-registry.com/podcast-helper:v1.1.0

# 또는 YAML 수정 후
kubectl apply -f k8s/deployment.yaml

# 롤아웃 상태 확인
kubectl rollout status deployment/podcast-helper-bot
```

## 8. 롤백

```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/podcast-helper-bot

# 특정 버전으로 롤백
kubectl rollout history deployment/podcast-helper-bot
kubectl rollout undo deployment/podcast-helper-bot --to-revision=2
```

## 트러블슈팅

### Pod가 시작되지 않는 경우

```bash
# Pod 상태 확인
kubectl describe pod <pod-name>

# 로그 확인
kubectl logs <pod-name>
```

### Secret을 찾을 수 없는 경우

```bash
# Secret 존재 확인
kubectl get secrets

# Secret 내용 확인 (base64 디코딩)
kubectl get secret podcast-helper-secrets -o yaml
```

### 이미지를 가져올 수 없는 경우

Private registry 사용 시 ImagePullSecret이 필요할 수 있습니다:

```bash
kubectl create secret docker-registry regcred \
  --docker-server=your-registry.com \
  --docker-username=your-username \
  --docker-password=your-password \
  --docker-email=your-email@example.com
```

그리고 `deployment.yaml`에 추가:

```yaml
spec:
  template:
    spec:
      imagePullSecrets:
      - name: regcred
      containers:
      - name: bot
        ...
```

## 리소스 정리

```bash
# Deployment 삭제
kubectl delete -f k8s/deployment.yaml

# Secret 삭제
kubectl delete secret podcast-helper-secrets
```

## 모니터링

### 리소스 사용량 확인

```bash
# Pod 리소스 사용량
kubectl top pod <pod-name>

# 노드 리소스 사용량
kubectl top nodes
```

### 이벤트 확인

```bash
kubectl get events --sort-by=.metadata.creationTimestamp
```

## 프로덕션 권장사항

1. **네임스페이스 사용**: 리소스 격리를 위해 별도 네임스페이스 생성
   ```bash
   kubectl create namespace podcast-helper
   kubectl apply -f k8s/ -n podcast-helper
   ```

2. **리소스 제한**: CPU/Memory limits를 실제 사용량에 맞게 조정

3. **Liveness Probe 추가**: 봇이 응답하지 않을 때 자동 재시작
   ```yaml
   livenessProbe:
     exec:
       command:
       - python
       - -c
       - "import sys; sys.exit(0)"  # 실제 헬스체크 로직으로 교체
     initialDelaySeconds: 30
     periodSeconds: 30
   ```

4. **로깅**: 중앙 로그 수집 시스템 연동 (ELK, Loki 등)

5. **시크릿 관리**: Vault, Sealed Secrets 등 사용

6. **이미지 태그**: `latest` 대신 버전 태그 사용 (예: `v1.0.0`)
