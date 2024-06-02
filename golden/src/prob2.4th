variable x
variable y
variable z
variable result

1 x !
1 y !
0 z !
0 result !

: find_sum  begin x @ y @ + z ! z @ 2 mod 0 = if result @ z @ + result ! then y @ x ! z @ y ! z @ 4000000 < until ;

find_sum

result ?
