release: prisma py fetch && prisma generate && prisma migrate deploy
web: uvicorn api.app.main:app --host=0.0.0.0 --port=${PORT}