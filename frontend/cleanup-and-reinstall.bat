@echo off
echo ========================================
echo Cleaning MetaMask SDK Dependencies
echo ========================================

echo.
echo Step 1: Removing node_modules...
if exist node_modules rmdir /s /q node_modules

echo.
echo Step 2: Removing package-lock.json...
if exist package-lock.json del /f package-lock.json

echo.
echo Step 3: Removing .next build cache...
if exist .next rmdir /s /q .next

echo.
echo Step 4: Installing clean dependencies...
call npm install

echo.
echo Step 5: Verifying no @metamask/sdk...
call npm list @metamask/sdk 2>nul
if %errorlevel% equ 0 (
    echo WARNING: @metamask/sdk still found!
) else (
    echo SUCCESS: No @metamask/sdk found
)

echo.
echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
echo Now run: npm run dev
echo.
pause
