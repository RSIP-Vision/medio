from functools import partial

from pydicom.uid import generate_uid

# Given by Medical Connections (http://www.medicalconnections.co.uk/FreeUID.html)
MEDIO_ROOT_UID = "1.2.826.0.1.3680043.10.513."


generate_uid = partial(generate_uid, prefix=MEDIO_ROOT_UID)
