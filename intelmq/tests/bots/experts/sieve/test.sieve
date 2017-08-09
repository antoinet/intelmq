if (source.ip == '127.0.0.1') {
  drop;
  add source.asn = 'as559'
}

if source.ip == '127.0.0.1' && source.asn == 'AS100' {
  add test = 'foobar'
}