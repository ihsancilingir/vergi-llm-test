#!/usr/bin/env bash
# =========================================================================
# tum_modeller.sh — Aynı deney kümesini üç model ailesinde arka arkaya
# koşturur (README metodolojik not 6: "mimari iddia tek modelde
# doğrulanamaz; aynı deseni en az 2-3 model ailesinde göstermek gerekir").
#
# Kullanım:
#   bash tum_modeller.sh                # tüm deneyler, tekrar=5
#   bash tum_modeller.sh "1,4" 10       # sadece deney 1 ve 4, tekrar=10
#
# Yargıç sabit tutulur (Anthropic/Claude): böylece Deney 2 ve 5'te üç
# test modeli AYNI yargıçla puanlanır ve modeller arası karşılaştırma
# yargıç farkından etkilenmez. (Claude'un kendisi test edilirken yargıcın
# aynı model olması öz-puanlama riski taşır; isterseniz o koşu için
# JUDGE_* değişkenlerini değiştirin.)
# =========================================================================
set -e

DENEY="${1:-hepsi}"
TEKRAR="${2:-5}"
JUDGE_PROVIDER="anthropic"
JUDGE_MODEL="claude-sonnet-4-6"

# Test edilecek modeller — gerekirse güncelleyin:
declare -A MODELLER=(
  [anthropic]="claude-sonnet-4-6"
  [openai]="gpt-4o"
  [gemini]="gemini-2.5-pro"
)

for provider in anthropic openai gemini; do
  model="${MODELLER[$provider]}"
  echo ""
  echo "############################################################"
  echo "#  ${provider} / ${model}  —  deney=${DENEY} tekrar=${TEKRAR}"
  echo "############################################################"
  python runner.py --deney "${DENEY}" \
    --provider "${provider}" --model "${model}" \
    --judge-provider "${JUDGE_PROVIDER}" --judge-model "${JUDGE_MODEL}" \
    --tekrar "${TEKRAR}"
done

echo ""
echo "Tüm koşular bitti. Tekil raporlar için:"
echo "  python report.py results/<dosya>.jsonl"
echo "Modeller arası çapraz rapor için:"
echo "  python capraz_rapor.py results/*.jsonl"
