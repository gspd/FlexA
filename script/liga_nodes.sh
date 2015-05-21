#!/bin/bash
               
	USUARIO="gspd"
	PASS="gspd"

	for ip in $(cat host.data);
		do
			echo -n "Iniciando FlexA-server em node $ip"
      		sshpass -p $PASS ssh $USUARIO@$ip "cd git/FlexA/ && git checkout send_parts > /dev/null 2>	/dev/null;  ./init_server.py > /dev/null & " &&
        	echo -e "\t\tOK"
		done
	
