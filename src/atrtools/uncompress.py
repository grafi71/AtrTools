class Uncompress:
	ASSEMBLY = ""
	DEFAULTS = {}

	def __init__(self, defaults=None):
		self.__defaults = defaults or self.__class__.DEFAULTS
		self.__assembly = self.__class__.ASSEMBLY.format(**self.defaults)
	
	@property
	def defaults(self):
		return self.__defaults

	@property 
	def assembly(self):
		return self.__assembly


class UncompressLegacy(Uncompress):
	DEFAULTS = {
		"SCREEN_SRC_L": "$C0",
		"SCREEN_SRC_H": "$C1",
		"SCREEN_LEN_L": "$C2",
		"SCREEN_LEN_H": "$C3",
		"SCREEN_DST_L": "$C4",
		"SCREEN_DST_H": "$C5",
		"SCREEN_TMP_L": "$C6",
		"SCREEN_TMP_H": "$C7",
		"LINE_BYTES" : 40,
		"ANTIC_LINE_SKIP": 102,
	}

	ASSEMBLY = """
SCREEN_SRC_L = {SCREEN_SRC_L}	; compressed source address
SCREEN_SRC_H = {SCREEN_SRC_H}

SCREEN_LEN_L = {SCREEN_LEN_L}	; size of compressed source
SCREEN_LEN_H = {SCREEN_LEN_H}

SCREEN_DST_L = {SCREEN_DST_L}	; destination address
SCREEN_DST_H = {SCREEN_DST_H}

SCREEN_TMP_L = {SCREEN_TMP_L}	; temporary register
SCREEN_TMP_H = {SCREEN_TMP_H}

		.proc uncompress
	    ldy #0
nextva0	lda (SCREEN_SRC_L), y	
		bne testbt1			
		ldx #128
putval0	tya
		jsr putbyte
		dex
		bne putval0
		jsr incrsrc
		jsr decsize
		bne nextva0
		rts

testbt1	cmp #128			
		bcs testbt2			
		tax					
		bne putval0			

testbt2	and #%01111111
		cmp #64		
		bcs uniqval

		and #%00111111
        bne nonzero
        lda #64
nonzero	tax
		jsr incrsrc
		jsr decsize
nextval	lda (SCREEN_SRC_L), y
		jsr putbyte
		dex
		bne nextval
        jsr incrsrc
		jsr decsize
		bne nextva0
		rts
	
uniqval and #%00111111
        bne nozero2
        lda #64       
nozero2	tax
		jsr incrsrc
nextva3	lda (SCREEN_SRC_L), y
		jsr putbyte
		jsr incrsrc	
		jsr decsize
		dex
		bne nextva3
		jsr decsize
		bne nextva0
		rts

putbyte sta (SCREEN_DST_L), y
		clc
		lda SCREEN_DST_L
		adc #1
		bcc noindst
		inc SCREEN_DST_H
noindst	sta SCREEN_DST_L
		clc
		lda SCREEN_TMP_L
		adc #1
		cmp #{LINE_BYTES}
		bne nonewli
		inc SCREEN_TMP_H
		lda SCREEN_TMP_H
		cmp #{ANTIC_LINE_SKIP}	
		bne nothalf		
		tya
		sta SCREEN_DST_L
		inc SCREEN_DST_H
nothalf	tya
nonewli	sta SCREEN_TMP_L
		rts

decsize	lda SCREEN_LEN_L
		sec
		sbc #1
		bcs nodeclh
		dec SCREEN_LEN_H
nodeclh	sta SCREEN_LEN_L
		lda SCREEN_LEN_L
		bne exitprc
		lda SCREEN_LEN_H
exitprc rts

incrsrc	lda SCREEN_SRC_L
		clc
		adc #1
		bcc noincsh
		inc SCREEN_SRC_H
noincsh	sta SCREEN_SRC_L
		rts
		.endp
"""

class UncompressLz4(Uncompress):
	ASSEMBLY = """
; CODE: xxl, fox
; SEE: https://xxl.atari.pl/lz4-decompressor/
; ENTRY: destination adress store in DEST
				.proc unlz4
                jsr    get_byte                  ; length of literals
                sta    token
:4 				lsr
                beq    read_offset               ; there is no literal
                cmp    #$0f
                jsr    getlength
literals        jsr    get_byte
                jsr    store
                bne    literals
read_offset     jsr    get_byte
                tay
                sec
                eor    #$ff
                adc    dest
                sta    src
                tya
                php
                jsr    get_byte
                plp
                bne    not_done
                tay
                beq    unlz4_done
not_done        eor    #$ff
                adc    dest+1
                sta    src+1
                ; c=1
                lda    #$ff
token           equ    *-1
                and    #$0f
                adc    #$03
                cmp    #$13
                jsr    getLength

@               lda    $ffff
src             equ    *-2
                inw    src
                jsr    store
                bne    @-
                beq    unlz4
store           sta    $ffff
dest            equ    *-2
                inw    dest
                dec    lenL
                bne    unlz4_done
                dec    lenH
unlz4_done      rts
getLength_next  jsr    get_byte
                tay
                clc
                adc    #$00
lenL            equ    *-1
                bcc    @+
                inc    lenH
@               iny
getLength       sta    lenL
                beq    getLength_next
                tay
                beq    @+
                inc    lenH
@               rts

lenH            .byte    $00

get_byte        lda    $ffff
source          equ    *-2
                inw    source
                rts
		        .endp
"""