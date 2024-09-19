from collections import defaultdict

from django.template.defaultfilters import slugify


class defaultdictNoStr(defaultdict):
    def __str__(self):
        raise ValueError("Don't use {tags} directly.")


def many_to_dictionary(field):
    # Converts ManyToManyField to dictionary by assuming, that field
    # entries contain an _ or - which will be used as a delimiter
    mydictionary = dict()

    for index, t in enumerate(field.all()):
        # Populate tag names by index
        mydictionary[index] = slugify(t.name)

        # Find delimiter
        delimiter = t.name.find("_")

        if delimiter == -1:
            delimiter = t.name.find("-")

        if delimiter == -1:
            continue

        key = t.name[:delimiter]
        value = t.name[delimiter + 1 :]

        mydictionary[slugify(key)] = slugify(value)

    return mydictionary
