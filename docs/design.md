## Sink diff

    $ sink diff api-A api-B api-C
      ---
      [+] added     [>] newer      [=] same
      [-] removed   [<] older      [.] origin
      [!] absent    [~] changed    
      ---
                                  [A] ← api-A
                                   | [B] ← api-B
                                   |  | [C] ← api-B
        0 src/api/service.py       >  <  - 
        1 src/api/config.py        +  !  !
        2 src/api/model.py         .  >  =
        3 src/api/server.py        .  =  <
      ---
      *   src/api/service.py       A  B
          [E]dit [s]kip [q]uit 
      …   src/api/service.py       A     C
          [E]dit [s]kip [q]uit 

      *   src/api/config.py        A  B
          [E]dit [s]kip [q]uit 
      …   src/api/config.py        A     B
          [E]dit [s]kip [q]uit 

## Sink snap

    $ sink snap dir
