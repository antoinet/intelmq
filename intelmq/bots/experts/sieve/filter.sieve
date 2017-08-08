
if allof ('source.ip' :is '192.168.13.13', 'feed.name' :contains 'cymru') { reject;keep }

if 'source.ip' :matches ['blaark', 'foo'] { reject }

if 'anumber' :eq 3 { keep }

