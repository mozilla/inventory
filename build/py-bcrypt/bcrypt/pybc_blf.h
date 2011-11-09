/* $OpenBSD: blf.h,v 1.6 2002/02/16 21:27:17 millert Exp $ */
/*
 * Blowfish - a fast block cipher designed by Bruce Schneier
 *
 * Copyright 1997 Niels Provos <provos@physnet.uni-hamburg.de>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. All advertising materials mentioning features or use of this software
 *    must display the following acknowledgement:
 *      This product includes software developed by Niels Provos.
 * 4. The name of the author may not be used to endorse or promote products
 *    derived from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
 * IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
 * IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
 * NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
 * THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef _PYBC_BLF_H_
#define _PYBC_BLF_H_

#if defined(_MSC_VER)
typedef unsigned __int8		u_int8_t;
typedef unsigned __int16	u_int16_t;
typedef unsigned __int32	u_int32_t;
#endif

/* Schneier specifies a maximum key length of 56 bytes.
 * This ensures that every key bit affects every cipher
 * bit.  However, the subkeys can hold up to 72 bytes.
 * Warning: For normal blowfish encryption only 56 bytes
 * of the key affect all cipherbits.
 */

#define BLF_N	16			/* Number of Subkeys */
#define BLF_MAXKEYLEN ((BLF_N-2)*4)	/* 448 bits */

/* Blowfish context */
typedef struct BlowfishContext {
	u_int32_t S[4][256];	/* S-Boxes */
	u_int32_t P[BLF_N + 2];	/* Subkeys */
} pybc_blf_ctx;

/* Raw access to customized Blowfish
 *	blf_key is just:
 *	Blowfish_initstate( state )
 *	Blowfish_expand0state( state, key, keylen )
 */

void pybc_Blowfish_initstate(pybc_blf_ctx *);
void pybc_Blowfish_expand0state(pybc_blf_ctx *, const u_int8_t *, u_int16_t);
void pybc_Blowfish_expandstate(pybc_blf_ctx *, const u_int8_t *, u_int16_t,
    const u_int8_t *, u_int16_t);

/* Standard Blowfish */

void pybc_blf_enc(pybc_blf_ctx *, u_int32_t *, u_int16_t);

/* Converts u_int8_t to u_int32_t */
u_int32_t pybc_Blowfish_stream2word(const u_int8_t *, u_int16_t, u_int16_t *);

#endif
