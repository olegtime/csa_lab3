variable username
64 cells allot

: save_username  64 0 do key dup username i cells + ! 0 = if leave then loop ;

: print_username  64 0 do username i cells + @ dup 0 = if leave then emit loop ;

." What is your name?"
cr
save_username
." Hello, "
print_username
." !"
