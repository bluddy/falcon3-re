	.286
	ifndef	??version
?debug	macro
	endm
publicdll macro	name
	public	name
	endm
$comm	macro	name,dist,size,count
	comm	dist name:BYTE:count*size
	endm
	else
$comm	macro	name,dist,size,count
	comm	dist name[size]:BYTE:count
	endm
	endif
	?debug	S "probe\t.c"
	?debug	C E910A84B5D0970726F62655C742E63
T_TEXT	segment byte public 'CODE'
T_TEXT	ends
DGROUP	group	_DATA,_BSS
	assume	cs:T_TEXT,ds:DGROUP
_DATA	segment word public 'DATA'
d@	label	byte
d@w	label	word
_DATA	ends
_BSS	segment word public 'BSS'
b@	label	byte
b@w	label	word
_BSS	ends
T_TEXT	segment byte public 'CODE'
   ;	
   ;	long far sub_1A6D4(unsigned a, unsigned n) {
   ;	
	assume	cs:T_TEXT
_sub_1A6D4	proc	far
	enter	4,0
	push	si
	mov	si,word ptr [bp+8]
   ;	
   ;	    long acc = 0;
   ;	
	mov	word ptr [bp-2],0
	mov	word ptr [bp-4],0
	jmp	short @1@74
@1@50:
   ;	
   ;	    while (n != 0) {
   ;	        acc += a;
   ;	
	mov	ax,word ptr [bp+6]
	add	word ptr [bp-4],ax
	adc	word ptr [bp-2],0
   ;	
   ;	        n--;
   ;	
	dec	si
@1@74:
	or	si,si
	jne	short @1@50
   ;	
   ;	    }
   ;	    return acc;
   ;	
	mov	dx,word ptr [bp-2]
	mov	ax,word ptr [bp-4]
   ;	
   ;	}
   ;	
	pop	si
	leave	
	ret	
_sub_1A6D4	endp
	?debug	C E9
T_TEXT	ends
_DATA	segment word public 'DATA'
s@	label	byte
_DATA	ends
T_TEXT	segment byte public 'CODE'
T_TEXT	ends
	public	_sub_1A6D4
	end
