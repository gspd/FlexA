#!/bin/bash
               
USUARIO="gspd"
PASS="gspd"

MASCARA_REDE="192.168.1."
HOST=(208 109 5)

for ip in "${HOST[@]}"
	do
		echo -e -n "Matando python em host 192.168.1.$ip\t"
	   	sshpass -p $PASS ssh $USUARIO@$MASCARA_REDE$ip "killall python3" &&
        echo -e "\t\tOK"
	done
	
