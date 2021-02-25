sudo pkill -f bin/ryu-manager
sleep 0.3
cp -R stretch/ Metrics/ times.txt /media/sf_SharedVM_RyuDRL/links-metrics/32nodos/OSPF_all/Ryu/TM-$1/
sleep 0.3
sudo sh clear.sh
