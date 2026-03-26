SHARED_DIR = packages/shared
GRPC_OUT = $(SHARED_DIR)/shared/grpc_generated
MARKETPLACE_STUBS = packages/marketplace/gateway_stubs

.PHONY: proto

proto:
	@mkdir -p $(MARKETPLACE_STUBS)
	docker compose run --rm -v ./$(MARKETPLACE_STUBS):/out -w /app/packages/shared scheduler \
		sh -c 'python -m grpc_tools.protoc \
		-I./shared/protos \
		--python_out=/out \
		--grpc_python_out=/out \
		./shared/protos/gateway.proto'
	@sed -i 's/^import gateway_pb2 as/from gateway_stubs import gateway_pb2 as/' \
		$(MARKETPLACE_STUBS)/gateway_pb2_grpc.py
	@touch $(MARKETPLACE_STUBS)/__init__.py
	@echo "Gateway stubs generated in $(MARKETPLACE_STUBS)"
