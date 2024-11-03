#!/bin/bash

source activate langchain

conda activate langchain

#bash ~/clash-for-linux/start.sh

#source /etc/profile.d/clash.sh

#proxy_on

#wget google.com

#rm index.html

python startup.py -a &


sleep 30



streamlit run webui.py
