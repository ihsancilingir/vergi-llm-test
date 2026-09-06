@echo off
REM =========================================================================
REM tum_modeller.bat -- Ayni deney kumesini alti model ailesinde arka arkaya
REM kosturur (README metodolojik not 6: "mimari iddia tek modelde
REM dogrulanamaz; ayni deseni en az 2-3 model ailesinde gostermek gerekir").
REM
REM Kullanim:
REM   tum_modeller.bat                # tum deneyler, tekrar=5
REM   tum_modeller.bat "1,4" 10       # sadece deney 1 ve 4, tekrar=10
REM
REM Yargic sabit tutulur (Anthropic/Claude): boylece test modelleri AYNI
REM yargicla puanlanir ve modeller arasi karsilastirma yargic farkindan
REM etkilenmez.
REM =========================================================================

set DENEY=%1
if "%DENEY%"=="" set DENEY=hepsi
set TEKRAR=%2
if "%TEKRAR%"=="" set TEKRAR=5
set JUDGE_PROVIDER=anthropic
set JUDGE_MODEL=claude-sonnet-4-6

echo.
echo ============================================================
echo   anthropic / claude-sonnet-4-6  --  deney=%DENEY% tekrar=%TEKRAR%
echo ============================================================
python runner.py --deney %DENEY% --provider anthropic --model claude-sonnet-4-6 --judge-provider %JUDGE_PROVIDER% --judge-model %JUDGE_MODEL% --tekrar %TEKRAR%
if errorlevel 1 (
    echo [HATA] Anthropic kosusu basarisiz oldu, devam ediliyor...
)

echo.
echo ============================================================
echo   openai / gpt-4o  --  deney=%DENEY% tekrar=%TEKRAR%
echo ============================================================
python runner.py --deney %DENEY% --provider openai --model gpt-4o --judge-provider %JUDGE_PROVIDER% --judge-model %JUDGE_MODEL% --tekrar %TEKRAR%
if errorlevel 1 (
    echo [HATA] OpenAI kosusu basarisiz oldu, devam ediliyor...
)

echo.
echo ============================================================
echo   gemini / gemini-3.6-flash  --  deney=%DENEY% tekrar=%TEKRAR%
echo ============================================================
python runner.py --deney %DENEY% --provider gemini --model gemini-3.6-flash --judge-provider %JUDGE_PROVIDER% --judge-model %JUDGE_MODEL% --tekrar %TEKRAR%
if errorlevel 1 (
    echo [HATA] Gemini kosusu basarisiz oldu, devam ediliyor...
)

echo.
echo ============================================================
echo   deepseek / deepseek-v4-flash  --  deney=%DENEY% tekrar=%TEKRAR%
echo ============================================================
python runner.py --deney %DENEY% --provider deepseek --model deepseek-v4-flash --judge-provider %JUDGE_PROVIDER% --judge-model %JUDGE_MODEL% --tekrar %TEKRAR%
if errorlevel 1 (
    echo [HATA] DeepSeek kosusu basarisiz oldu, devam ediliyor...
)

echo.
echo ============================================================
echo   grok / grok-4.6  --  deney=%DENEY% tekrar=%TEKRAR%
echo ============================================================
python runner.py --deney %DENEY% --provider grok --model grok-4.6 --judge-provider %JUDGE_PROVIDER% --judge-model %JUDGE_MODEL% --tekrar %TEKRAR%
if errorlevel 1 (
    echo [HATA] Grok kosusu basarisiz oldu, devam ediliyor...
)

echo.
echo ============================================================
echo   kumru / vngrs-ai/Kumru-2B  --  deney=%DENEY% tekrar=%TEKRAR%
echo ============================================================
python runner.py --deney %DENEY% --provider kumru --model vngrs-ai/Kumru-2B --judge-provider %JUDGE_PROVIDER% --judge-model %JUDGE_MODEL% --tekrar %TEKRAR%
if errorlevel 1 (
    echo [HATA] Kumru kosusu basarisiz oldu, devam ediliyor...
)

echo.
echo Tum kosular bitti. Tekil raporlar icin:
echo   python report.py results\^<dosya^>.jsonl
echo Modeller arasi capraz rapor icin:
echo   python capraz_rapor.py results\*.jsonl --cikti results\capraz_rapor.md
