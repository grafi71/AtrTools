
UNCOMPRESS6502 = """
SCREEN_SRC_L = $C0	; compressed source address
SCREEN_SRC_H = $C1

SCREEN_LEN_L = $C2	; size of compressed source
SCREEN_LEN_H = $C3

SCREEN_DST_L = $C4	; destination address
SCREEN_DST_H = $C5

SCREEN_TMP_L = $C6	; temporary register
SCREEN_TMP_H = $C7

        ; Uncompress SCREEN_SRC data to SCREEN_DST address.
        ; Size of SCREEN_SRC must be provided in SCREEN_LEN
        ; Temporary registers SCREEN_TMP must be set to zero
		.proc uncompress
	    ldy #0
nxtval	lda (SCREEN_SRC_L), y	; load next compressed data byte
		bne testhb			; if not zero
		ldx #128			; zero, so repeat 128 zero-values
putval	tya
		jsr putbyte
		dex
		bne putval
		jsr incrsrc
		jsr decsize
		bne nxtval
		rts

		; highest bit is zero, other bits are not zero -> 0 repeated from 1 to 127 times
testhb	cmp #128			; check highest bit
		bcs bitset			; jump if bit is set
		; zero so we repeat 0-values (max 64)
		tax					; number of 0-values
		bne putval			; jump (only non-zero value in x)

		; zero values done, now check for single value repeat

bitset	and #%01111111
		cmp #64		
		bcs unique

		; 10 command -> next value is repeated (we repeat next value)

		and #%00111111	; no of repeats
        bne nozero1
        lda #64
nozero1	tax
		jsr incrsrc
		jsr decsize
next1	lda (SCREEN_SRC_L), y	; load value to be repeated
		jsr putbyte
		dex
		bne next1
        jsr incrsrc
		jsr decsize
		bne nxtval
		rts

unique	; repeated value done, now just putbyte unique values (11 command)
		and #%00111111	; no of repeats of unique values
        bne nozero2
        lda #64         ; if A is zero the number of repeats is 64
nozero2	tax
		jsr incrsrc
next2	lda (SCREEN_SRC_L), y	; load unique value
		jsr putbyte
		jsr incrsrc			; incremenrt source
		jsr decsize
		dex
		bne next2
		jsr decsize
		bne nxtval
		rts

        ; store acumulator value to destination, increment destination, Y must be set to zero!
putbyte sta (SCREEN_DST_L), y
		clc
		lda SCREEN_DST_L
		adc #1
		bcc noinch
		inc SCREEN_DST_H
noinch	sta SCREEN_DST_L
		; increment line counter
		clc
		lda SCREEN_TMP_L
		adc #1
		cmp #40
		bne nonew
		inc SCREEN_TMP_H	; line counter
		lda SCREEN_TMP_H
		cmp #102		; 4k boundary ? 102*40=4080
		bne nohalf		
		; boundary, add 16 bytes to get to next 4k segment
		tya
		sta SCREEN_DST_L
		inc SCREEN_DST_H
		; done
nohalf	tya
nonew	sta SCREEN_TMP_L
		rts

decsize ; decrement size of data to decompress
		lda SCREEN_LEN_L
		sec
		sbc #1
		bcs nodec
		dec SCREEN_LEN_H
nodec	sta SCREEN_LEN_L
		lda SCREEN_LEN_L
		bne exitp
		lda SCREEN_LEN_H
exitp   ; test then state of N flag to check for empty buffer 
		rts

incrsrc ; increment source address
		lda SCREEN_SRC_L
		clc
		adc #1
		bcc noincs
		inc SCREEN_SRC_H
noincs	sta SCREEN_SRC_L
		rts
		.endp
"""
class RepeatedValues:
    def __init__(self, value, repeats):
        self.value = value
        self.repeats = repeats

    def __repr__(self):
        return '{}(value={},repeats={})'.format(self.__class__.__name__, self.value, self.repeats)

    def export(self, table):
        "Export compressed values to buffer table"
        cmd = 128 if not self.value else 64

        for _ in range(0, self.repeats//cmd):
            table.append(0b00000000 if not self.value else 0b10000000) # 64 or 128 repeats
            if self.value: 
                table.append(self.value)

        rst = self.repeats%cmd
        if rst:
            table.append(0b00000000|rst if not self.value else 0b10000000|rst) # 64 or 128 repeats
            if self.value:
                table.append(self.value)

    def adjust_last(self, value):
        "Cannot adjust"
        return False

class UniqueValues:
    def __init__(self, values):
        self.values = values

    def __repr__(self):
        return '{}(values={})'.format(self.__class__.__name__, self.values)

    def export(self, table):
        "Export compressed values to buffer table"
        idx = 0
        for _ in range(0, len(self.values)//64):
            table.append(0b11000000) # 64 repeats
            table.extend(self.values[idx:idx+64])
            idx += 64
        rst = len(self.values)%64
        if rst:
            table.append(0b11000000 | rst)
            table.extend(self.values[idx:])
           
    def adjust_last(self, value):
        "Append value to values"
        self.values.append(value)
        return True

class Compress:
    "Compressor class"

    def __init__(self, data):
        "Construct object from byte data."
        self.data = data
        self.len = len(data)
        self.compressed = []
        self.packed = []

    def compress(self):
        "Compress method"
        idx = 0
        while idx < self.len-1:
            cnt = 0
            while idx < self.len-1 and self.data[idx] == self.data[idx+1]:
                cnt += 1
                idx += 1
            if cnt:
                self.compressed.append(RepeatedValues(self.data[idx], cnt+1))
                idx += 1 
            else:
                buf = []
                while idx < self.len-1 and self.data[idx] != self.data[idx+1]:
                    buf.append(self.data[idx])
                    idx += 1
                if buf:
                    self.compressed.append(UniqueValues(buf))
        
        if idx != self.len:
            lst = self.data[-1]
            if self.compressed:
                if not self.compressed[-1].adjust_last(lst):
                    self.compressed.append(UniqueValues([lst]))
            else:
                self.compressed.append(UniqueValues([lst]))

    def pack(self):
        "Pack data to Atari format"
        for data in self.compressed:
            data.export(self.packed)
