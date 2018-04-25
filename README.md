# ciscoPremiseCollabMgmt
Building Python modules to simplify use of provisioning API's for the Cisco on-premise collab product suite; AXL, SQL, RIS, CUPI, etc.  Hammer approach: to provide quick operation and simplistic consumption, some modules forego WSDL file consumption and build envelopes by hand (may revisit in future to see whether caching can help).  Where API's don't exist, some SSH helpers are provided to allow scripting of other things possible on the CLI.

Arranged in modules and classes by product and API\transport respectively:
```
└───cucm.py: Cisco Communications Manager classes:
│               axl: Administrative XML used for wide-ranging provisioning tasks
│               controlcenter: control services running on a node    
└───cuc.py: Cisco Unity Connection classes:
|               TBD
└───vos.py
                ssh: CLI and CLI-SQL helper functions for Cisco VoiceOS Redhat platforms
```
