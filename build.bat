@echo off
echo Building frontend...
cd frontend
call npm install
call npm run build
cd ..

echo Copying dist to backend/frontend_dist...
if exist backend\frontend_dist rmdir /s /q backend\frontend_dist
xcopy /e /i frontend\dist backend\frontend_dist

echo Done! backend/frontend_dist is ready.
