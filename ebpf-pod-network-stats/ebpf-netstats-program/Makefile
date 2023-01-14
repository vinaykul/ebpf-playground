# SPDX-License-Identifier: GPL-2.0-or-later

CLANG=clang
CLANGFLAGS= -I.\
                        -Wno-unused-value -Wno-pointer-sign\
                        -Wno-compare-distinct-pointer-types \
                        -Wno-gnu-variable-sized-type-not-at-end \
                        -Wno-address-of-packed-member -Wno-tautological-compare \
                        -Wno-unknown-warning-option -O1 -emit-llvm -c -o -
LLC=llc -march=bpf -filetype=obj

bpfsrc = $(wildcard *.c)
bpfobj = $(bpfsrc:.c=.o)

all: tcbpf
	mkdir -p obj
	mv *.o obj/

tcbpf: $(bpfobj)

%.o: %.c
	$(CLANG) -c $^ $(CLANGFLAGS) | $(LLC)  -o $@

clean:
	rm -rf obj

