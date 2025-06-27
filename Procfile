web: uvicorn api.app.main:app --host=0.0.0.0 --port=${PORT}
release: prisma generate && prisma migrate deploy