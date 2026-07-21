# Deployment to AWS EKS - Progress Tracker

## Steps — ✅ ALL COMPLETED

- [x] Create TODO.md
- [x] 1. Update `outputs/backend/database.py` - Add DB_PATH env var support
- [x] 2. Update `AIConversation/outputs/backend/database.py` - Same change (sync copy)
- [x] 3. Update `Dockerfile` - Ensure `/data` directory exists
- [x] 4. Create `k8s/namespace.yaml`
- [x] 5. Create `k8s/configmap.yaml`
- [x] 6. Create `k8s/pvc.yaml`
- [x] 7. Create `k8s/hpa.yaml`
- [x] 8. Update `k8s/deployment.yaml` - PVC mount, probes, env vars, ConfigMap ref
- [x] 9. Update `k8s/service.yaml` - Added name field to port, namespace
- [x] 10. Create `scripts/build-and-push.sh` - ECR build & push script
- [x] 11. Create `scripts/deploy-eks.sh` - EKS deployment script
- [x] 12. Update `README.md` - Full AWS EKS deployment section

