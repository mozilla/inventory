/*
 * Copyright (c) 2006 Damien Miller <djm@mindrot.org>
 *
 * Permission to use, copy, modify, and distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 */

#include "Python.h"

#if defined(_MSC_VER)
typedef unsigned __int8		u_int8_t;
typedef unsigned __int16	u_int16_t;
typedef unsigned __int32	u_int32_t;
#endif

/* $Id: bcrypt_python.c,v 1.3 2009/10/01 13:09:52 djm Exp $ */

/* Import */
char *pybc_bcrypt(const char *, const char *);
void encode_salt(char *, u_int8_t *, u_int16_t, u_int8_t);

PyDoc_STRVAR(bcrypt_encode_salt_doc,
"encode_salt(csalt, log_rounds) -> encoded_salt\n\
    Encode a raw binary salt and the specified log2(rounds) as a\n\
    standard bcrypt text salt. Used internally by bcrypt.gensalt()\n");

static PyObject *
bcrypt_encode_salt(PyObject *self, PyObject *args, PyObject *kw_args)
{
	static char *keywords[] = { "csalt", "log_rounds", NULL };
	char *csalt = NULL;
	int csaltlen = -1;
	long log_rounds = -1;
	char ret[64];

	if (!PyArg_ParseTupleAndKeywords(args, kw_args, "s#l:encode_salt",
	    keywords, &csalt, &csaltlen, &log_rounds))
                return NULL;
	if (csaltlen != 16) {
		PyErr_SetString(PyExc_ValueError, "Invalid salt length");
		return NULL;
	}
	if (log_rounds < 4 || log_rounds > 31) {
		PyErr_SetString(PyExc_ValueError, "Invalid number of rounds");
		return NULL;
	}
	encode_salt(ret, csalt, csaltlen, log_rounds);
	return PyString_FromString(ret);
}

PyDoc_STRVAR(bcrypt_hashpw_doc,
"hashpw(password, salt) -> hashed_password\n\
    Hash the specified password and the salt using the OpenBSD\n\
    Blowfish password hashing algorithm. Returns the hashed password.\n");

static PyObject *
bcrypt_hashpw(PyObject *self, PyObject *args, PyObject *kw_args)
{
	static char *keywords[] = { "password", "salt", NULL };
	char *password = NULL, *salt = NULL;
	char *ret;

	if (!PyArg_ParseTupleAndKeywords(args, kw_args, "ss:hashpw", keywords,
	    &password, &salt))
                return NULL;

	char *password_copy = strdup(password);
	char *salt_copy = strdup(salt);

	Py_BEGIN_ALLOW_THREADS;
	ret = pybc_bcrypt(password_copy, salt_copy);
	Py_END_ALLOW_THREADS;

	free(password_copy);
	free(salt_copy);
	if ((ret == NULL) ||
	    strcmp(ret, ":") == 0) {
		PyErr_SetString(PyExc_ValueError, "Invalid salt");
		return NULL;
	}

	return PyString_FromString(ret);
}

static PyMethodDef bcrypt_methods[] = {
	{	"hashpw",	(PyCFunction)bcrypt_hashpw,
		METH_VARARGS|METH_KEYWORDS,	bcrypt_hashpw_doc	},
	{	"encode_salt",	(PyCFunction)bcrypt_encode_salt,
		METH_VARARGS|METH_KEYWORDS,	bcrypt_encode_salt_doc	},
	{NULL,		NULL}		/* sentinel */
};

PyDoc_STRVAR(module_doc, "Internal module used by bcrypt.\n");

PyMODINIT_FUNC
init_bcrypt(void)
{
	PyObject *m;

	m = Py_InitModule3("bcrypt._bcrypt", bcrypt_methods, module_doc);
	PyModule_AddStringConstant(m, "__version__", "0.1");
}

