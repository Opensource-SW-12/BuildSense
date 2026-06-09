#!/usr/bin/env python3
"""
정적 PassMark DB 빌더 (KAN-165)

PassMark 웹사이트에서 수집한 원시 데이터를 처리해 정적 JSON DB를 생성합니다.
생성된 파일은 passmark_tiering.py의 라이브 스크래핑 대신 사용됩니다.

  CPU: 80,000점 기준, 멀티스레드 점수 사용
  GPU: 41,588점(GeForce RTX 5090 D, 최고점) 기준

사용법:
  cd BuildSense
  python tools/build_passmark_static_db.py
"""
import json
import re
from pathlib import Path

BASE_DIR   = Path(__file__).parent.parent
SPECS_DIR  = BASE_DIR / "data" / "specs"

CPU_MAX  = 80_000
GPU_MAX  = 41_588   # GeForce RTX 5090 D
MAX_TIER = 29

# ── 원시 CPU 데이터 (cpubenchmark.net/multithread/) ───────────────────────
CPU_RAW = """\
AMD Ryzen Threadripper 9980X|143,003
AMD Ryzen Threadripper PRO 9985WX|151,377
AMD Ryzen Threadripper 7980X|135,642
AMD Ryzen Threadripper PRO 7985WX|131,837
AMD Ryzen Threadripper 9970X|107,215
AMD Ryzen Threadripper PRO 9975WX|105,068
AMD Ryzen Threadripper 7960X|83,410
AMD Ryzen Threadripper PRO 7975WX|95,489
AMD Ryzen Threadripper PRO 9965WX|92,687
AMD Ryzen Threadripper 9960X 24-Cores|92,579
Intel Core Ultra 7 270K Plus|68,752
Intel Core Ultra 9 285K|67,271
AMD Ryzen Threadripper PRO 9955WX|67,107
AMD Ryzen 9 9950X|65,762
AMD Ryzen 9 PRO 9965X3D|64,196
Intel Core Ultra 9 290HX Plus|63,130
AMD Ryzen 9 9955HX3D|62,710
AMD Ryzen Threadripper PRO 3975WX|62,226
AMD Ryzen 9 7950X3D|62,321
AMD Ryzen 9 7950X|62,180
AMD Ryzen Threadripper PRO 7955WX|60,056
Intel Core i9-13900KS|60,488
Intel Core i9-14900KS|60,063
AMD Ryzen Threadripper PRO 5965WX|65,886
Intel Core Ultra 7 265K|58,664
Intel Core Ultra 7 265KF|58,560
Intel Core i9-14900K|58,333
Intel Core i9-14900KF|58,200
Intel Core i9-13900K|58,166
AMD Ryzen 9 7945HX3D|57,735
Intel Core Ultra 9 285|57,567
Intel Core i9-13900KF|57,539
Intel Core Ultra 9 285HX|57,190
AMD Ryzen 9 9900X3D|56,196
AMD Ryzen 9 9955HX|56,076
AMD Ryzen Threadripper PRO 9945WX|55,939
Intel Core Ultra 9 275HX|55,864
AMD Ryzen AI Max+ 395|55,050
AMD Ryzen Threadripper 3960X|54,784
AMD Ryzen 9 9900X|54,411
AMD Ryzen 9 7945HX|54,080
AMD Ryzen 9 7940HX|53,325
Intel Core Ultra 5 250K Plus|52,188
Intel Core i7-14700KF|52,084
Intel Core i7-14700K|51,989
AMD Ryzen 9 9850HX|51,722
AMD Ryzen AI Max+ Pro 395|51,643
AMD Ryzen 9 8945HX|51,518
AMD Ryzen 9 7900X|51,262
AMD Ryzen 9 8940HX|50,238
AMD Ryzen 9 7900X3D|50,213
Intel Core Ultra 7 265|49,726
AMD Ryzen Threadripper PRO 7945WX|49,673
Intel Core Ultra 7 265F|49,494
Intel Core Ultra 5 250KF Plus|46,743
Intel Core i9-14900F|46,645
Intel Core i7-13700K|45,684
Intel Core i7-13700KF|45,565
Snapdragon X2 Elite Extreme - X2E94100|45,506
Intel Core i9-13980HX|45,501
AMD Ryzen 9 5950X|45,292
Intel Core i9-13900|44,873
Intel Core i9-14900|44,806
AMD Ryzen 9 7845HX|44,661
AMD RYZEN AI MAX+ 392|44,617
Intel Core i9-14900HX|44,031
AMD Ryzen 9 5900XT|43,872
Intel Core i9-12900KS|43,409
Intel Core Ultra 5 245KF|43,171
Intel Core Ultra 5 245K|43,143
AMD Ryzen 7 8840HX|43,117
Intel Core i9-13900T|42,613
Intel Core i7-13790F|42,218
Intel Core i9-13900HX|41,765
Intel Core i7-14700F|41,400
AMD Ryzen 7 7840HX|41,365
AMD Ryzen 7 9850X3D|41,339
Snapdragon X2 Elite - X2E88100|41,265
Intel Core i9-12900K|41,133
Intel Core Ultra 5 235HX|40,759
Intel Core i9-13950HX|40,681
Intel Core i9-12900KF|40,570
Intel Core i7-14700|40,552
Intel Core i9-13900E|40,326
AMD Ryzen Threadripper PRO 5945WX|40,161
Intel Core Ultra 5 235|40,031
AMD Ryzen 7 9800X3D|39,966
AMD Ryzen Threadripper PRO 3955WX|39,874
Intel Core Ultra 9 285T|39,873
AMD Ryzen 9 5900X|38,911
Intel Core Ultra 5 245|38,495
Intel Core i5-14600K|38,452
AMD Ryzen 9 3950X|38,435
Intel Core Ultra 5 235A|38,392
Intel Core i5-14600KF|38,354
Intel Core i7-14790F|38,351
Intel Core Ultra 7 265T|38,105
AMD Ryzen 7 PRO 9755|38,100
Intel Core i7-13700F|37,863
Intel Core i5-13600K|37,519
AMD Ryzen AI 9 HX 470|37,502
Intel Core Ultra 5 245HX|37,472
Intel Core i5-13600KF|37,369
AMD Ryzen 7 PRO 9745|37,082
AMD Ryzen 7 9700X|37,040
AMD Ryzen 7 9700F|37,006
Intel Core 9 273PE|36,810
Intel Core i7-14700HX|36,733
Intel Core Ultra X9 388H|36,454
Intel Core i7-13850HX|36,262
Intel Core i7-13700|36,002
Intel Core i5-14600|35,970
Intel Core i9-12900F|35,759
AMD Ryzen 7 7700X|35,532
AMD Ryzen AI 9 HX 375|35,361
Intel Core Ultra 9 386H|35,354
AMD Ryzen AI 9 HX 370|35,059
AMD Ryzen AI 9 HX PRO 470|34,863
AMD Ryzen 7 PRO 7745|34,826
AMD Ryzen 7 7700|34,361
AMD Ryzen 7 7800X3D|34,281
Intel Core i7-12700K|34,278
Intel Core Ultra 9 285H|34,261
Intel Core Ultra 7 265H|34,145
Intel Core Ultra 7 356H|34,105
AMD Ryzen 9 5900|33,972
Intel Core i7-12700KF|33,968
Intel Core i9-12900|33,643
Intel Core i7-14650HX|33,617
Intel Core Ultra X7 358H|33,728
AMD Ryzen AI 9 HX PRO 375|33,530
AMD Ryzen AI Max 385|33,476
AMD Ryzen Threadripper PRO 3945WX|33,414
Intel Core i7-13700E|33,280
AMD Ryzen AI 9 HX PRO 370|33,250
Intel Core i9-12900HX|33,093
Intel Core Ultra 7 366H|33,045
Intel Core Ultra 5 230F|32,916
AMD RYZEN AI MAX+ 388|32,709
Intel Core i9-13900F|48,379
Intel Core i9-14900F|46,645
AMD Ryzen 9 3900X|32,490
AMD Ryzen 9 3900XT|32,482
AMD Ryzen AI 9 H 465|32,465
AMD Ryzen 7 7700G|32,432
AMD Ryzen 7 7745HX|32,344
AMD Ryzen Threadripper 2990WX|32,058
AMD Ryzen AI Max Pro 385|32,026
Intel Core i7-13700HX|31,792
AMD Ryzen 7 8700G|31,550
AMD Ryzen 7 8745HX|31,525
AMD Ryzen 5 PRO 9645|31,434
Intel Core Ultra 5 235T|31,417
Intel Core i5-13600|31,410
AMD Ryzen 9 PRO 3900|31,232
Intel Core i7-12800HX|31,221
Intel Core i9-12950HX|31,146
AMD Ryzen 7 PRO 8700G|31,142
Intel Core 5 223PE|31,124
Intel Core Ultra 5 225F|31,066
AMD Ryzen 7 8700F|30,991
Intel Core i5-14500|30,921
Intel Core i7-14700T|30,879
Intel Core i5-13500|30,873
Intel Core Ultra 5 245T|30,752
Intel Core Ultra 7 255H|30,725
AMD Ryzen 9 3900|30,587
Intel Core i7-12850HX|30,550
AMD Ryzen AI 9 H 365|30,514
Intel Core Ultra 5 225|30,444
Intel Core i9-14901E|30,298
Intel Core i7-12700F|30,209
AMD Ryzen 5 9600X|30,087
Intel Core 7 251TE|30,022
AMD Ryzen 9 8945H|29,979
Intel Core i7-12700|29,904
AMD Ryzen 9 7940HS|29,848
Intel Core Ultra 5 235H|29,846
Intel Core i9-13905H|29,683
AMD Ryzen Threadripper 2950X|29,458
AMD Ryzen 9 8945HS|29,367
AMD Ryzen 5 9600|29,286
Intel Core 7 253PE|29,271
AMD Ryzen AI 9 465|29,220
Intel Core i7-13645HX|29,215
AMD Ryzen 7 8745H|29,185
AMD Ryzen 9 270|29,129
Intel Core Ultra 9 185H|29,104
Intel Core Ultra 5 338H|28,869
Intel Core i9-12900T|28,852
AMD Ryzen 7 H 255|28,740
AMD Ryzen 7 PRO 8845HS|28,726
AMD Ryzen 7 8745HS|28,677
Intel Core 9 270H|28,628
AMD Ryzen 9 7940H|28,449
Intel Core i7-12700E|28,437
AMD Ryzen 5 9500F|28,424
AMD Ryzen 7 7840HS|28,386
AMD Ryzen 7 8845HS|28,381
Intel Core Ultra 5 225H|28,348
AMD Ryzen 7 5800X3D|28,302
AMD Ryzen 5 7600X|28,293
AMD Ryzen 7 PRO 8700GE|28,288
AMD Ryzen 7 260|28,182
Intel Core i9-12900E|28,170
AMD Ryzen 7 5800XT|28,037
Intel Core i9-9940X @ 3.30GHz|28,007
AMD Ryzen 7 PRO 8840H|27,994
Intel Core i5-13600T|27,951
AMD Ryzen Threadripper 1950X|27,766
AMD Ryzen 7 5800X|27,679
Intel Core i9-10940X @ 3.30GHz|27,670
Intel Core i5-13500HX|27,646
Intel Core i7-13700T|27,599
Intel Core i9-7960X @ 2.80GHz|27,590
AMD Ryzen 5 PRO 7645|27,564
Intel Core i5-12600K|27,528
Intel Core i5-12600KF|27,527
Intel Core 5 213PE|27,488
Intel Core i5-13600HX|27,438
AMD Ryzen 7 7840H|27,189
Intel Core i9-13900H|27,154
AMD Ryzen 9 PRO 7940HS|27,096
Intel Core 7 250H|27,030
Intel Core i5-13400E|27,000
AMD Ryzen 5 7600|26,976
Intel Core i9-13900HK|26,829
AMD Ryzen 9 6980HX|26,817
AMD Ryzen 7 PRO 7840HS|26,803
Intel Core i5-13490F|26,744
Intel Core i5-14600T|26,734
Intel Core i9-12900H|26,722
AMD Ryzen 7 8845H|26,682
AMD Ryzen 7 PRO 8840HS|26,654
AMD Ryzen 7 5700X|26,584
AMD Ryzen 5 7500F|26,551
Intel Core i5-13500E|26,340
AMD Ryzen 7 5700X3D|26,308
Intel Core i7-12800HE|26,307
AMD Ryzen AI 7 450|26,262
AMD Ryzen AI 7 H 350|26,253
Intel Core i7-13800H|26,227
AMD Ryzen 5 7645HX|26,224
Intel Core Ultra 3 205|26,193
AMD Ryzen AI 7 PRO 450|26,176
Intel Core i7-14701E|26,103
AMD Ryzen 7 PRO 5845|26,054
Intel Core i7-13700H|25,950
AMD Ryzen Threadripper 2990X|25,874
Intel Core Ultra 7 165H|25,862
AMD Ryzen 5 7600X3D|25,839
AMD Ryzen 7 5800|25,719
Intel Core Ultra 5 225T|25,621
Intel Core i7-13705H|25,544
Intel Core i5-14400F|25,525
AMD Ryzen 5 7400F|25,514
AMD Ryzen 7 250|25,298
AMD Ryzen 5 PRO 8600G|25,277
Intel Core i9-7940X @ 3.10GHz|25,228
Intel Core i9-12900HK|25,217
AMD Ryzen Threadripper 2920X|25,213
AMD Ryzen 5 8600G|25,198
Intel Core Ultra 5 336H|25,187
Intel Core i5-14400|25,119
AMD Ryzen 5 7500X3D|25,112
Intel Core i7-12700H|25,100
Intel Core 7 253PTE|25,031
Intel Core i9-11900K @ 3.50GHz|24,947
Intel Core i5-13400F|24,944
AMD Ryzen AI 7 350|24,927
Intel Core i7-14701TE|24,821
Intel Core i9-9920X @ 3.50GHz|24,760
Intel Core i5-13450HX|24,649
AMD Ryzen Z1 Extreme|24,639
Intel Core Ultra 7 155H|24,577
Intel Core i9-11900KF @ 3.50GHz|24,528
AMD Ryzen 7 H 250|24,508
AMD Ryzen AI Max Pro 380|24,431
AMD Ryzen 5 8400F|24,420
AMD Ryzen 7 PRO 7840U|24,391
AMD Ryzen 7 7840U|24,386
Intel Core 7 240H|24,353
Intel Core i7-11700K @ 3.60GHz|24,341
AMD Ryzen 7 5700G|24,266
AMD Ryzen 7 5700|24,244
AMD Ryzen 9 6900HX|24,115
AMD Ryzen AI 7 PRO 350|24,108
Intel Core 9 273PTE|24,054
AMD Ryzen 7 PRO 8840U|23,992
Intel Core 5 211EF|23,988
Intel Core i7-12800H|23,868
AMD Ryzen 7 PRO 5755G|23,858
Intel Core i5-13400|23,855
Intel Core 5 211E|23,833
AMD Ryzen 9 PRO 6950H|23,832
Intel Core i7-11700KF @ 3.60GHz|23,819
AMD Ryzen 7 PRO 5750G|23,784
Intel Core i5-14450HX|23,712
AMD Ryzen 5 PRO 8600GE|23,710
AMD Ryzen Z2 Extreme|23,649
Intel Core i5-12600HL|23,615
AMD Ryzen 5 PRO 8645HS|23,569
Intel Core i9-7920X @ 2.90GHz|23,557
AMD Ryzen 5 PRO 8645HS|23,569
Intel Core i5-13600HE|23,483
AMD Ryzen 7 3800XT|23,426
AMD Ryzen 7 8840U|23,369
Snapdragon X2 Elite - X2E90100|34,732
Qualcomm Snapdragon X Elite - X1E001DE|31,863
Qualcomm Snapdragon X Elite - X1E-84-100|24,809
"""

# ── 원시 GPU 데이터 (videocardbenchmark.net/high_end_gpus.html) ──────────
GPU_RAW = """\
GeForce RTX 5090 D|41,588
GeForce RTX 5090|38,950
GeForce RTX 4090|38,072
RTX PRO 6000 Blackwell Workstation Edition|37,990
GeForce RTX 5080|35,686
GeForce RTX 4080|34,454
GeForce RTX 4080 SUPER|34,257
RTX PRO 4500 Blackwell|33,460
RTX PRO 5000 Blackwell|32,951
GeForce RTX 5070 Ti|32,397
GeForce RTX 4070 Ti SUPER|31,840
GeForce RTX 4070 Ti|31,566
Radeon RX 7900 XTX|31,427
GeForce RTX 4090 D|31,056
RTX 5000 Ada Generation|30,334
GeForce RTX 4070 SUPER|29,948
GeForce RTX 3090 Ti|29,279
Radeon RX 7900 XT|29,043
GeForce RTX 5070|28,722
RTX 6000 Ada Generation|28,663
RTX PRO 4000 Blackwell|28,348
RTX 4500 Ada Generation|28,265
GeForce RTX 5090 Laptop GPU|28,235
Radeon RX 6950 XT|28,082
Radeon PRO W7900|27,729
Radeon RX 7900 GRE|27,424
Radeon PRO W7800|27,300
Radeon AI PRO R9700|27,248
GeForce RTX 4090 Laptop GPU|27,074
Radeon RX 9070 XT|26,906
GeForce RTX 4070|26,890
GeForce RTX 3080 Ti|26,759
Radeon RX 6900 XT|26,689
GeForce RTX 3080 12GB|26,564
GeForce RTX 3090|26,532
Radeon Pro V620|26,519
GeForce RTX 5080 Laptop GPU|26,346
Radeon RX 9070|25,397
RTX 5880 Ada Generation|25,096
Radeon RX 6800 XT|25,055
GeForce RTX 3080|25,004
GeForce RTX 4080 Laptop GPU|24,736
Radeon RX 7800 XT|24,386
RTX PRO 5000 Blackwell Generation Laptop GPU|24,359
Radeon RX 9070 GRE|24,025
RTX 4000 Ada Generation|23,646
RTX PRO 4000 Blackwell Generation Laptop GPU|23,263
RTX 5000 Ada Generation Laptop GPU|23,246
GeForce RTX 3070 Ti|23,218
RTX 3500 Ada Generation Embedded GPU|22,926
RTX A5000|22,880
Radeon PRO W7700|22,868
Radeon RX 7700 XT|22,702
RTX A6000|22,657
GeForce RTX 5060 Ti 16GB|22,636
GeForce RTX 4060 Ti 16GB|22,610
GeForce RTX 4060 Ti|22,609
GeForce RTX 5070 Ti Laptop GPU|22,545
RTX 4000 Ada Generation Laptop GPU|22,191
GeForce RTX 5060 Ti 8GB|22,134
GeForce RTX 3070|22,108
Radeon RX 6800|22,049
NVIDIA A10|21,687
GeForce RTX 2080 Ti|21,452
RTX PRO 3000 Blackwell Generation Laptop GPU|21,277
RTX A5500|21,192
Radeon RX 7700|21,015
GeForce RTX 5060|20,755
Radeon RX 6750 XT|20,708
RTX PRO 5000 72GB Blackwell|20,656
RTX A4500|20,634
RTX PRO 2000 Blackwell|20,530
RTX 4000 SFF Ada Generation|20,509
GeForce RTX 3060 Ti|20,250
Radeon RX 6750 GRE 12GB|20,155
Radeon PRO W6800|20,122
Radeon RX 9060 XT 16GB|20,101
TITAN RTX|19,922
Quadro RTX 8000|19,859
Radeon RX 9060 XT 8GB|19,782
Radeon RX 6700 XT|19,731
TITAN V|19,720
RTX 3500 Ada Generation Laptop GPU|19,716
GeForce RTX 4070 Laptop GPU|19,505
GeForce RTX 4060|19,502
GeForce RTX 2080 SUPER|19,440
RTX A4000|19,362
GeForce RTX 5070 Laptop GPU|19,156
Radeon RX 6750 GRE 10GB|18,979
Radeon RX 6700|18,935
GeForce RTX 3080 Ti Laptop GPU|18,908
NVIDIA TITAN Xp|18,754
GeForce GTX 1080 Ti|18,594
GeForce RTX 2080|18,584
TITAN Xp COLLECTORS EDITION|18,531
Quadro GV100|18,414
GeForce RTX 2070 SUPER|18,134
Radeon RX 7650 GRE|17,925
Quadro RTX 6000|17,789
NVIDIA A10G|17,660
Radeon RX 9060|17,640
Radeon Pro W6900X|17,413
GeForce RTX 3070 Ti Laptop GPU|17,408
GeForce RTX 4060 Laptop GPU|17,376
Radeon RX 6850M XT|17,311
Radeon RX 7600 XT|17,308
RTX A5500 Laptop GPU|17,231
RTX 2000 Ada Generation|17,141
Radeon RX 6650 XT|17,116
GeForce RTX 5050|17,065
RTX 5000 Ada Generation Embedded GPU|17,056
GeForce RTX 3060|16,938
RTX A4000H|16,768
GeForce RTX 3060 12GB|16,724
Radeon Pro W6800X|16,619
Radeon RX 5700 XT 50th Anniversary|16,528
Radeon RX 7600|16,481
GeForce RTX 2060 SUPER|16,467
Radeon RX 6600 XT|16,445
RTX A5000 Laptop GPU|16,365
RTX PRO 2000 Blackwell Generation Laptop GPU|16,352
Radeon PRO W7600|16,306
Radeon VII|16,253
GeForce RTX 3080 Laptop GPU|16,124
Radeon RX 6650M XT|16,081
Radeon RX 5700 XT|16,065
GeForce RTX 2070|16,063
RTX 3000 Ada Generation Laptop GPU|16,062
Intel Arc B580|15,991
GeForce RTX 2060 12GB|15,926
Radeon RX 6800S|15,723
Radeon Pro Vega II|15,618
GeForce GTX 1080|15,606
RTX 2000E Ada Generation|15,503
Radeon RX 7600S|15,496
Radeon RX 7700S|15,471
Quadro P6000|15,390
Quadro RTX 5000|15,327
GeForce RTX 3060 8GB|15,231
Radeon RX 6650M|15,194
Radeon Pro W5700X|15,179
GeForce RTX 3070 Laptop GPU|15,066
Radeon RX 6600|15,056
Intel Arc Pro B60|15,049
Radeon RX 6700S|15,020
GeForce RTX 2080 (Mobile)|15,014
Radeon PRO W6600|14,980
Quadro RTX 4000|14,849
RTX 2000 Ada Generation Laptop GPU|14,842
Quadro RTX 5000 (Mobile)|14,832
RTX A4000 Laptop GPU|14,824
RTX PRO 1000 Blackwell Generation Laptop GPU|14,777
GeForce GTX 1070 Ti|14,672
Radeon RX 7600M XT|14,549
GeForce RTX 4050 Laptop GPU|14,258
GeForce RTX 5050 Laptop GPU|14,255
Radeon RX 5700|14,226
Radeon Pro W5700|14,124
Intel Arc B570|14,105
GeForce RTX 2060|14,094
Radeon RX 6600 LE|14,000
Quadro GP100|13,983
Radeon RX Vega 64|13,873
Radeon RX 6600M|13,866
RTX A2000 12GB|13,672
NVIDIA TITAN X|13,660
Radeon Pro VII|13,649
GeForce GTX 980 Ti|13,634
Radeon RX 6700M|13,629
RTX 1000 Ada Generation Laptop GPU|13,582
Radeon RX 6600S|13,569
GeForce GTX 1070|13,514
RTX A2000|13,419
Radeon RX 5600 XT|13,398
Radeon Pro Vega 64X|13,369
Intel Arc A770|13,356
Radeon RX 6800M|13,283
Radeon PRO W7500|13,220
GeForce RTX 3060 Laptop GPU|13,122
RTX PRO 500 Blackwell Generation Laptop GPU|13,115
Radeon PRO W6600X|13,113
Radeon RX Vega 56|12,969
Radeon Pro Vega 64|12,886
Radeon Vega Frontier Edition|12,705
GeForce GTX 1660 SUPER|12,677
Quadro RTX 5000 with Max-Q Design|12,660
Quadro P5000|12,652
GeForce RTX 2080 with Max-Q Design|12,633
RTX A3000 Laptop GPU|12,628
Intel Arc A750|12,627
GeForce GTX 1660 Ti|12,618
GeForce GTX TITAN X|12,564
GeForce RTX 3050 8GB|12,491
Radeon Pro WX 8200|12,469
Quadro P5200 with Max-Q Design|12,464
Radeon Pro 5700 XT|12,457
Radeon RX 5600 OEM|12,426
Tesla V100-PCIE-16GB|12,328
Radeon Pro V520 MxGPU|12,258
Quadro RTX 4000 with Max-Q Design|12,207
Radeon Pro Vega 56|12,065
Intel Arc A580|12,050
GeForce RTX 3050 Laptop GPU|12,003
Radeon PRO W6600M|11,998
Radeon RX 7400|11,909
Intel Arc A770M|11,882
GeForce RTX 3050 OEM|11,874
Radeon Pro WX 9100|11,795
Radeon RX 5600|11,753
Quadro M6000|11,712
Quadro RTX 4000 (Mobile)|11,692
GeForce GTX 1080 with Max-Q Design|11,679
GeForce GTX 1660|11,616
Quadro M6000 24GB|11,500
Quadro P4200 with Max-Q Design|11,472
Radeon Pro 5700|11,457
Quadro P4000|11,418
GeForce RTX 2070 with Max-Q Design|11,401
GeForce RTX 2060 (Mobile)|11,353
Radeon Pro Vega 48|11,270
Quadro P5200|11,240
RTX 500 Ada Generation Laptop GPU|11,199
GeForce GTX 980|11,080
RTX A1000|10,747
Radeon RX 7600M|10,999
Radeon Pro SSG|10,972
GeForce RTX 3050 6GB|10,747
Quadro RTX 3000|10,661
GeForce GTX 1650 SUPER|10,193
Quadro P4200|10,152
GeForce RTX 3050 6GB Laptop GPU|10,140
GeForce GTX 1660 Ti (Mobile)|10,097
GeForce RTX 3050 Ti Laptop GPU|10,079
GeForce GTX 1060|10,040
RTX A1000 6GB Laptop GPU|10,030
Intel Arc A730M|9,808
Intel Arc Pro A60|9,798
GeForce GTX 1060 3GB|9,841
GeForce GTX 970|9,638
GeForce RTX 2060 with Max-Q Design|9,629
Radeon RX 6500 XT|9,625
Radeon R9 Fury|9,530
GeForce RTX 3050 4GB Laptop GPU|9,503
RTX A2000 Laptop GPU|9,474
GeForce GTX 780 Ti|9,451
RTX A1000 Laptop GPU|9,433
Quadro P2200|9,414
Radeon R9 Fury X|9,391
Quadro M5000|9,358
Radeon Pro 5600M|9,304
Radeon RX 590|9,290
Radeon R9 390X|9,201
Radeon RX 5500 XT|9,066
Intel Arc B390 GPU|8,973
Radeon Pro W5500|8,952
Radeon RX 5500|8,855
Radeon R9 295X2|8,816
Radeon R9 390|8,802
Radeon RX 5600M|8,797
Radeon RX 580|8,789
GeForce GTX 1660 Ti with Max-Q Design|8,616
Radeon RX 480|8,529
Quadro P3200|8,514
Radeon R9 290X|8,436
Radeon PRO W6400|8,392
Radeon R9 290X / 390X|8,380
Radeon Pro Duo|8,329
Radeon RX590 GME|8,310
GeForce GTX Titan|8,196
GeForce GTX 1060 (Mobile)|8,160
Radeon R9 290 / 390|8,150
Radeon R9 290|8,149
Quadro RTX 3000 with Max-Q Design|8,139
Intel Arc B370 GPU|8,106
Intel Arc A530M|8,045
GeForce GTX 780|7,961
Radeon RX 470|7,918
GeForce GTX 1650|7,873
Radeon Pro 5500 XT|7,869
NVIDIA T1200 Laptop GPU|7,840
GeForce GTX 1060 with Max-Q Design|7,817
Radeon Pro 580|7,753
Radeon RX 6400|7,742
Radeon Pro WX 7100|7,723
GeForce RTX 2050|7,713
NVIDIA T1000 8GB|7,678
Radeon RX 6500|7,676
GeForce GTX 1650 Ti|7,535
GeForce GTX 580|4,629
Quadro P1000|4,508
GeForce GTX 1050 Ti|6,364
GeForce GTX 1650 with Max-Q Design|6,348
Radeon Pro 570|6,337
Quadro P3000|6,326
Intel Arc A380|6,310
GeForce MX570 A|6,266
GeForce GTX 960|6,144
Radeon R9 380X|6,127
Radeon R9 280X|6,077
Radeon RX 5500M|6,039
RTX A400|5,997
GeForce GTX 770|5,961
Radeon R9 380|5,957
Intel Arc Pro A30M|5,862
GeForce MX570|5,812
Radeon Pro 5300M|5,803
Intel Arc Pro A40/A50|5,697
Radeon RX 5300M|5,397
GeForce GTX 670|5,371
GeForce GTX 950|5,353
Quadro P2000 with Max-Q Design|5,347
RTX5000-Ada-4Q|5,298
GeForce GTX 1050 Ti (Mobile)|5,918
Intel Arc Pro A30M|5,862
Radeon Pro Vega 20|5,169
Radeon R9 M295X|5,150
Radeon R9 M395X|5,126
Intel Arc A370M|5,115
GeForce GTX 1050 3GB|5,115
Radeon RX 5300|7,603
GeForce GTX 1650 Ti with Max-Q Design|6,636
GeForce GTX 1050 Ti with Max-Q Design|5,315
GeForce GTX 760 Ti|5,307
Radeon Pro WX 5100|5,465
Intel Arc A310|5,465
Radeon R9 380|5,957
Quadro K5200|6,177
GeForce GTX 960|6,144
NVIDIA T1000|7,653
GeForce GTX 1050|5,049
Radeon Pro W5500M|3,470
Quadro M4000|6,678
Radeon Pro 460|3,453
Quadro P620|3,710
Radeon RX 560|3,682
Radeon Pro 560X|3,678
GeForce GTX 1650 (Mobile)|6,968
GeForce GTX 1050 with Max-Q Design|3,901
GeForce GTX 750 Ti|3,900
GeForce GTX 680|5,607
Radeon R9 270X|4,871
Radeon R9 270|4,306
Radeon HD 7990|5,566
Radeon R9 285|6,680
Radeon RX 460|4,098
GeForce GTX 480|4,078
GeForce GTX 660|4,050
Quadro M2000|4,049
GeForce MX450|3,718
GeForce GTX 760|4,825
NVIDIA T500|3,618
NVIDIA T600 Laptop GPU|7,059
NVIDIA T600|6,370
NVIDIA A10G|17,660
Intel Arc B390 GPU RI|8,902
Intel Arc 140T GPU|6,617
Intel Arc Pro 140T GPU|6,612
Intel Arc 130T GPU|6,138
Intel Arc Pro 130T GPU|6,127
Intel Arc 140V GPU|5,141
Intel Arc 130V GPU|4,501
Radeon PRO W6300|5,560
Radeon Pro WX 4100|3,688
Intel Arc Pro B50|12,568
Intel Arc Pro B70|18,847
RTX PRO 4000 Blackwell SFF Edition|24,252
Radeon RX 9060 XT 16GB|20,101
Radeon RX 9060 XT 8GB|19,782
Radeon RX 9060|17,640
Radeon RX 9070|25,397
Radeon RX 9070 XT|26,906
Radeon RX 9070 GRE|24,025
Radeon 610M Ryzen 7 7840HX|20,904
RTX A3000 12GB Laptop GPU|13,841
Quadro K2200|3,579
T400|3,615
T550 Laptop GPU|4,728
Quadro T2000|7,271
Quadro T1000|6,511
Quadro T2000 with Max-Q Design|7,018
Quadro T1000 with Max-Q Design|6,628
RTX 2000 Ada Generation Embedded GPU|13,842
"""

# ── CPU 제외 규칙 ─────────────────────────────────────────────────────────

# 이름에 아래 문자열이 포함되면 서버/워크스테이션/Mac CPU로 제외
_CPU_EXCL_CONTAINS = [
    "EPYC",
    "Xeon",
    "Threadripper PRO",   # 워크스테이션/서버 플랫폼 (일반 Threadripper 제외 유지)
    "Apple M",            # Mac CPU
    "Neoverse",           # ARM 서버
    "Altra",              # ARM 서버
    "Hygon",              # 중국 서버 CPU
    "Jintide",            # 중국 서버 CPU
    "Arc G3 Extreme",     # CPU 목록에 잘못 포함된 GPU
    "Virtual @",          # 가상 머신 항목
    "ARM Cortex",
    "ARM Neoverse",
    "ARM Ampere",
    "Ampere ARM",
]

# 이름이 아래 문자열로 시작하면 제외
_CPU_EXCL_STARTSWITH = [
    "ARM ",               # ARM 서버/임베디드 범용 항목
]


def _is_excluded_cpu(name: str) -> bool:
    if any(name.startswith(p) for p in _CPU_EXCL_STARTSWITH):
        return True
    return any(ex in name for ex in _CPU_EXCL_CONTAINS)


# ── GPU 제외 규칙 ─────────────────────────────────────────────────────────

_GPU_EXCL_CONTAINS = [
    "USB Display",
    "spacedesk",
    "DameWare",
    "VMware",
    "OrayIdd",
    "CXDisplay",
    "LuminonCore",
    "MacroSilicon",
    "EPSON Projector",
    "Racer-Tech",
    "extension Adapter",
    "Miracast",
    "LIANLI USB",
    "AicUsbDisplay",
    "TURZX",
    "Eng Sample",
    "Radeon Eng Sample",
    "MxGPU",               # AMD 가상 GPU 파티션
    "SQExtFramebuffer",
    "B8DKMDAP",
    "Winsta0",
    "SMI USB",
    "with Radeon Graphics", # APU 내장 그래픽 벤치마크
    "P102-100",
    "P104-100",
    "P106-100",
    "CMP 40HX",
    "CMP 30HX",
    "Radeon Instinct",     # 데이터센터
    "FirePro S",           # 서버용
    "Barco MXRV",
    "Barco MXRT",
    "Matrox LUMA",
    "EIZO",
    "DisplayLink",
    "Inspiration",
    "RTX5000-Ada-4Q",      # 가상 파티션
]

_GPU_EXCL_STARTSWITH = [
    "GRID ",               # NVIDIA 가상 GPU
    "Tesla ",              # NVIDIA 데이터센터
    "nVidia L",            # NVIDIA L-시리즈 데이터센터
    "A100",
    "Ryzen ",              # GPU 목록에 포함된 APU/CPU 항목
    "RadeonT ",            # 중복/오분류 항목
    "RTXA",                # RTXA6000-8Q 등 가상 파티션
    "RTX6000-Ada-",        # 가상 파티션
    "RTX5000-Ada-",        # 가상 파티션
    "FirePro S",
    "Q12U-",
    "A2-4Q",
    "AMD Ryzen Z1 Extreme", # GPU 목록의 CPU 항목
    "Radeon Ryzen",
]

# iGPU 계열 패턴 (정규식)
_GPU_EXCL_REGEX = [
    r"^Radeon \d{3}M",     # Radeon 610M, 680M, 780M 등 내장 GPU
    r"^Radeon \d{4}S",     # Radeon 8040S, 8050S 등 내장 GPU
    r"Ryzen [579]\s",      # APU 벤치마크 항목 (GPU 목록 내)
    r"Ryzen 7 \d{4}",
    r"Ryzen 9 \d{4}",
    r"Ryzen 5 \d{4}",
    r"^L[0-9]",            # L2, L4, L20, L40, L40S 데이터센터
    r"^A[0-9]{2}-",        # A10-, A16-, A40- 데이터센터 파티션
    r"Radeon 610M|Radeon 660M|Radeon 680M|Radeon 760M|Radeon 780M",
    r"Radeon 840M|Radeon 860M|Radeon 880M|Radeon 890M",
    r"Radeon 8040S|Radeon 8050S|Radeon 8060S",
    r"^NVIDIA A40-",       # 데이터센터 파티션
    r"Radeon Ryzen",       # APU 항목
]


def _is_excluded_gpu(name: str) -> bool:
    if any(name.startswith(p) for p in _GPU_EXCL_STARTSWITH):
        return True
    if any(ex in name for ex in _GPU_EXCL_CONTAINS):
        return True
    for pat in _GPU_EXCL_REGEX:
        if re.search(pat, name):
            return True
    return False


# ── 파싱 & 빌드 ──────────────────────────────────────────────────────────

def _parse_entry(line: str):
    parts = line.strip().split("|")
    if len(parts) != 2:
        return None
    name = parts[0].strip()
    score_str = parts[1].strip().replace(",", "")
    try:
        score = int(score_str)
    except ValueError:
        return None
    if not name or score <= 0:
        return None
    return name, score


def _calc_tier(score: int, max_score: int) -> int:
    return int(score / max_score * MAX_TIER)


def build_db(raw: str, max_score: int, filter_fn, label: str) -> list[dict]:
    seen: set[str] = set()
    items: list[dict] = []
    skipped_filter = 0
    skipped_tier   = 0
    skipped_dup    = 0

    for line in raw.strip().splitlines():
        entry = _parse_entry(line)
        if not entry:
            continue
        name, score = entry

        if name in seen:
            skipped_dup += 1
            continue
        seen.add(name)

        if filter_fn(name):
            skipped_filter += 1
            continue

        tier = _calc_tier(score, max_score)
        if tier < 1:
            skipped_tier += 1
            continue

        items.append({"name": name, "score": score, "price_usd": "NA"})

    items.sort(key=lambda x: x["score"], reverse=True)
    print(
        f"{label}: {len(items)}개 유지 "
        f"(제외-필터 {skipped_filter}, 제외-티어0 {skipped_tier}, 중복 {skipped_dup})"
    )
    return items


def main():
    SPECS_DIR.mkdir(parents=True, exist_ok=True)

    cpu_items = build_db(CPU_RAW, CPU_MAX, _is_excluded_cpu, "CPU")
    gpu_items = build_db(GPU_RAW, GPU_MAX, _is_excluded_gpu, "GPU")

    cpu_path = SPECS_DIR / "cpu_passmark_static.json"
    gpu_path = SPECS_DIR / "gpu_passmark_static.json"

    cpu_path.write_text(json.dumps(cpu_items, ensure_ascii=False, indent=2), encoding="utf-8")
    gpu_path.write_text(json.dumps(gpu_items, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n저장 완료:")
    print(f"  {cpu_path}")
    print(f"  {gpu_path}")

    # 티어별 분포 미리보기
    for label, items, max_s in [("CPU", cpu_items, CPU_MAX), ("GPU", gpu_items, GPU_MAX)]:
        tier_dist: dict[int, int] = {}
        for item in items:
            t = _calc_tier(item["score"], max_s)
            tier_dist[t] = tier_dist.get(t, 0) + 1
        print(f"\n{label} 티어 분포:")
        for t in sorted(tier_dist):
            print(f"  Tier {t:2d}: {tier_dist[t]}개")


if __name__ == "__main__":
    main()
