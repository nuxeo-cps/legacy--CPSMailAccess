/*
(C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
Author: Tarek Ziadé <tz@nuxeo.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as published
by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
02111-1307, USA.

CPSMailAccess extensions, used to speed up some word processing
some of this code has been taken from TextIndexNG2, by Andreas Jung
*/

#include "Python.h"

typedef struct
{
    PyObject_HEAD
    PyObject * table;
    char *encoding;
}
Normalizer;

static char NormalizerType__doc__[] = "Normalizer object";


static void Normalizer_dealloc(Normalizer *self)
{
    Py_DECREF(self->table);
    PyMem_DEL(self);
}

static PyObject *getTable(Normalizer *self,PyObject *word)
{
    Py_XINCREF(self->table);
    return self->table;
}

static PyObject *NormalizeWord(Normalizer *self,PyObject *word)
{
    int i;
    PyObject *temp;

    if (PyString_Check(word)) {
        if (! (temp = PyUnicode_FromEncodedObject(word,self->encoding,"strict"))) {
            PyErr_SetString(PyExc_UnicodeError,"unicode conversion failed");
            return NULL;
        }
    }  else  {
        temp = PyUnicode_FromObject(word);
    }

    for (i=0; i<PyList_Size(self->table); i++) {
        PyObject *s, *item, *key, *value;

        item = PySequence_Fast_GET_ITEM(self->table, i);

        key   = PyTuple_GetItem(item,0);
        value = PyTuple_GetItem(item,1);

        if (! (s = PyUnicode_Replace( temp, key, value, -1)))
            return NULL;

        Py_DECREF(temp);

        temp = s;
    }

    return temp;
}

static PyObject *normalize(Normalizer *self, PyObject *args)
{
    int j;
    PyObject * data=NULL ;

    if (! (PyArg_ParseTuple(args,"O", &data)))
        return NULL;

    if (PyList_Check(data)) {
        PyObject *list;

        list = PyList_New(0);

        data = PySequence_Fast(data, "object must be sequence");

        for (j=0; j<PyList_Size(data); j++) {
            PyObject *word=NULL,*item=NULL;

            item = PySequence_Fast_GET_ITEM(data,j);
            word = NormalizeWord(self, item);
            PyList_Append(list, word);
        }

        return list;

    } else if (PyUnicode_Check(data) || PyString_Check(data) ) {

        PyObject *word=NULL;

        if (! (word = NormalizeWord(self,data)))
            return NULL;

        return (PyObject *) word;

    } else {
        PyErr_SetString(PyExc_TypeError,"argument must be unicode or string");
        return NULL;
    }

    return data;
}

static struct PyMethodDef Normalizer_methods[] =
{
    { "getTable", (PyCFunction)getTable,
        METH_VARARGS, "getTable()"
        "-- return the normalization table"
    },
    { "normalize", (PyCFunction)normalize,
        METH_VARARGS, "normalize([string],[or list]) "
        "-- normalize a string or a list of strings/unicode strings"
    },
    { NULL, NULL }      /* sentinel */
};

static  PyObject *Normalizer_getattr(Normalizer *self, char *name)
{
    return Py_FindMethod(Normalizer_methods, (PyObject *)self, name);
}

static PyTypeObject NormalizerType = {
                                         PyObject_HEAD_INIT(NULL)
                                         0,                            /*ob_size*/
                                         "Normalizer",                 /*tp_name*/
                                         sizeof(Normalizer),           /*tp_basicsize*/
                                         0,                            /*tp_itemsize*/
                                         /* methods */
                                         (destructor)Normalizer_dealloc,  /*tp_dealloc*/
                                         (printfunc)0,                 /*tp_print*/
                                         (getattrfunc)Normalizer_getattr, /*tp_getattr*/
                                         (setattrfunc)0,               /*tp_setattr*/
                                         (cmpfunc)0,                   /*tp_compare*/
                                         (reprfunc)0,                  /*tp_repr*/
                                         0,                            /*tp_as_number*/
                                         0,                            /*tp_as_sequence*/
                                         0,                            /*tp_as_mapping*/
                                         (hashfunc)0,                  /*tp_hash*/
                                         (ternaryfunc)0,               /*tp_call*/
                                         (reprfunc)0,                  /*tp_str*/

                                         /* Space for future expansion */
                                         0L,0L,0L,0L,
                                         NormalizerType__doc__            /* Documentation string */
                                     };


static char *Normalizer_args[]={"translation","encoding",NULL};

void CopyTranslationTable(Normalizer *self, PyObject *table)
{
    int i;
    self->table = PyList_New(0);
    table = PySequence_Fast(table, "argument must be sequence");

    for (i=0; i<PyObject_Length(table); i++)
    {
        PyObject *item, *key, *value, *tp;

        item = PySequence_Fast_GET_ITEM(table, i);

        key   = PyTuple_GetItem(item,0);
        value = PyTuple_GetItem(item,1);

        if (PyString_Check(key))
            key = PyUnicode_FromEncodedObject(key, self->encoding, "strict");
        else Py_XINCREF(key);

        if (PyString_Check(value))
            value = PyUnicode_FromEncodedObject(value, self->encoding, "strict");
        else Py_XINCREF(value);

        tp = Py_BuildValue("(OO)",key,value);
        PyList_Append(self->table, tp);

        Py_DECREF(tp);
        Py_DECREF(value);
        Py_DECREF(key);
    }

    Py_DECREF(table);
}

int checkList(PyObject *o)
{
    int i;
    PyObject *item,*key,*value;


    if ( !( PyList_Check(o) || PyTuple_Check(o) )) {
        PyErr_SetString(PyExc_TypeError, "argument must be list or tuple of 2-tuples of strings");
        return 0;
    }

    for (i=0;i<PySequence_Size(o); i++) {
        item = PySequence_GetItem(o,i);

        if (! PyTuple_Check(item)) {
            PyErr_SetString(PyExc_TypeError,"nested arguments must be tuples");
            goto err;
        }

        if (PyTuple_Size(item) != 2) {
            PyErr_SetString(PyExc_TypeError,"nested arguments must be 2-tuples of strings/unicode strings");
            goto err;
        }

        key = PyTuple_GetItem(item,0);
        value = PyTuple_GetItem(item,1);

        if (! (PyString_Check(key) || PyUnicode_Check(key))) {
            PyErr_SetString(PyExc_TypeError, "arg 1 or 2-tuple must be string or unicode");
            goto err;
        }

        if (! (PyString_Check(value) || PyUnicode_Check(value))) {
            PyErr_SetString(PyExc_TypeError, "arg 2 or 2-tuple must be string or unicode");
            goto err;
        }

        Py_DECREF(item);
    }
    return 1;

err:
    Py_DECREF(item);
    return 0;
}

static PyObject *normalizer(PyObject *modinfo, PyObject *args, PyObject *keywds)
{
    Normalizer *self=NULL;
    PyObject *table;
    char * encoding = "latin1";

    if (!(PyArg_ParseTupleAndKeywords(args, keywds, "O|s", Normalizer_args,
                                      &table, &encoding)))
        return NULL;

    if (!(self = PyObject_NEW(Normalizer, &NormalizerType)))
        return NULL;

    if (!checkList(table))
        return NULL;

    self->encoding = encoding;

    CopyTranslationTable(self,table);

    return (PyObject*) self;
}


static struct PyMethodDef cmailaccess_module_methods[] =
    {
        { "Normalizer", (PyCFunction) normalizer,
          METH_VARARGS|METH_KEYWORDS,
          "Normalizer(list of words, [encoding='latin1')"
          "-- Normalizer module - takes a list of 2-tuples of strings/unicode strings"
        },
        { NULL, NULL }
    };


void initcmailaccess(void)
{
    Py_InitModule3("cmailaccess", cmailaccess_module_methods,
                   "CPSMailAccess C Extensions");
}


