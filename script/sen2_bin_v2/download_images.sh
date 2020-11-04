#!/bin/bash
names="S2A_MSIL2A_20190411T151711_N0211_R125_T18LTM_20190411T205454 S2A_MSIL2A_20190411T151711_N0211_R125_T18LTN_20190411T205454 S2A_MSIL2A_20190411T151711_N0211_R125_T18LUM_20190411T205454 S2B_MSIL2A_20200420T151659_N0214_R125_T18LTN_20200420T210637 S2B_MSIL2A_20200420T151659_N0214_R125_T18LTM_20200420T210637 S2B_MSIL2A_20200220T151659_N0214_R125_T18LUM_20200220T205816"

for n in $names; do
  sentinelsat -d --name $n
done
