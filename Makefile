REGISTRY=ghcr.io
IMAGE_NAME=preinpost/podcast-helper
IMAGE_TAG=v1.0.0

build-arm64:
	docker build --platform linux/arm64 -t $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) .

build-amd64:
	docker build --platform linux/amd64 -t $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) .

build-multiarch:
	docker buildx create --use --name multiarch_builder || true
	docker buildx build --platform linux/arm64,linux/amd64 -t $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) --push .