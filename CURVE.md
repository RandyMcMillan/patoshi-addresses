
```python                                                                                                                                                          
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798                                                                                          
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8                                                                                          
print('secp256k1 G:')                                                                                                                                            
print(f'  Gx = {Gx:#066x}')                                                                                                                                      
print(f'  Gy = {Gy:#066x}')                                                                                                                                      
print(f'  Uncompressed pubkey (04 + Gx + Gy):')                                                                                                                  
print(f'  04{format(Gx, "064x")}{format(Gy, "064x")}')                                                                                                           
```                                                                                                                                                                

                                                                                                                                                                      
                                                                                                                                                                      ```bash                                                                                                                                                            
     python3 -c "                                                                                                                                                     
     # secp256k1 generator point G                                                                                                                                    
     Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798                                                                                          
     Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8                                                                                          
     print('secp256k1 G:')                                                                                                                                            
     print(f'  Gx = {Gx:#066x}')                                                                                                                                      
     print(f'  Gy = {Gy:#066x}')                                                                                                                                      
     print(f'  Uncompressed pubkey (04 + Gx + Gy):')                                                                                                                  
     print(f'  04{format(Gx, \\\"064x\\\")}{format(Gy, \\\"064x\\\")}')                                                                                               
     "                                                                                                                                                                
```                                                                                                                                                            