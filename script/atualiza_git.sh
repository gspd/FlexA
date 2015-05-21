#!/bin/bash
               
	USUARIO="gspd"
	PASS="gspd"

	for ip in $(cat host.data);
		do
			echo "Atualizando FlexA em node $ip "
      		sshpass -p $PASS ssh $USUARIO@$ip "cd git/FlexA/ && git pull > /dev/null ;" &&
        	echo -e "\t\tOK\n"
		done
	
