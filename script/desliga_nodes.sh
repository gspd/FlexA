#!/bin/bash
               
USUARIO="gspd"
PASS="gspd"

for ip in $(cat host.data);
	do
		echo -e -n "Matando python em host $ip\t"
	   	sshpass -p $PASS ssh $USUARIO@$ip "killall python3" &&
        echo -e "\t\tOK"
	done
	
