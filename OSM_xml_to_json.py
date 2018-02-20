#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
from collections import defaultdict
import pandas as pd


FILE = './DisneyWorld.osm'

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\.\t\r\n]')
lower_dot = re.compile(r'^([a-z]|_)*.([a-z]|_)*$')
numbers_only = re.compile('[^0-9]')
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
phonechars = re.compile(r'[(+).\-\. ]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

#this dataset has users that have char outside of ASCII char set.
#Replacing non printable chars with a ?
def remove_non_ascii(text):
    return re.sub(r'[^\x00-\x7F]+','?', text)

def count_postcodes(filename):
    postcodes = {}
    for event, elem in ET.iterparse(filename, events=('start', 'end')):
        if event == 'end':
            key = elem.attrib.get('k')
            if key == 'addr:postcode':
                postcode = clean_postcodes(elem.attrib.get('v'))
                if postcode[:5] not in postcodes:
                    postcodes[postcode[:5]] = 1
                else:
                    postcodes[postcode[:5]] += 1
    return postcodes

def clean_postcodes(zip):
    zip = numbers_only.sub('', zip)
    if len(zip) == 5:
        return zip
    else:
        return zip[:5]

mapping = { "St": "Street","St.": "Street","Ave" : "Avenue","Ave." : "Avenue","Blvd" : "Boulevard","Blvd." : "Boulevard",
            "Dr" : "Drive","Dr." : "Drive","Ct" : "Court","Ct." : "Court","Pl" : "Place","Pl." : "Place","Sq" : "Square",
            "Sq." : "Square","Ln" : "Lane","Ln." : "Lane","Rd" : "Road","Rd." : "Road","Tr" : "Trail","Tr." : "Trail",
            "Pkwy" : "Parkway","Pkwy." : "Parkway","Cmns" : "Commons","Cmns." : "Commons","N." : "North","N" : "North",
            "W." : "West","W" : "West","S." : "South","S" : "South","E." : "East","E" : "East" }



def update_name(name, mapping):
    nameArr = name.split(" ")
    for i in range(len(nameArr)):
        if nameArr[i] in mapping:
            nameArr[i] = mapping[nameArr[i]]
    name = " ".join(nameArr)
    return name

def clean_phone(phone, char_replace):
    phone = phonechars.sub("",phone)
    if char_replace:
        if bool(re.search(r'[aA-zZ]', phone)):
            return replace_chars(phone)
    if phone.startswith('1'):
        return phone[1:]
    if phone.startswith('01'):
        return phone[2:]
    return phone

#So we have some phone numbers that have Char in them. Need to convert to numbers
def replace_chars(phone):
    try:
        translationdict = str.maketrans("abcdefghijklmnopqrstuvwxyz","22233344455566677778889999")
    except AttributeError:
        import string
        translationdict = string.maketrans("abcdefghijklmnopqrstuvwxyz","22233344455566677778889999")

    correct_phone = phone.lower().translate(translationdict)
    return correct_phone

def shape_element(element):
    if element.tag == "node":
        #creates a basic model for the data
        node = {
            "id": element.attrib['id'],
            "type": "node",
            "pos": None,
            "created" : {
                "changeset": None,
                "user": None,
                "version": None,
                "uid": None,
                "timestamp": None
            }
        }
        #iterates through the fields of the CREATER array and adds the to the node
        for i in CREATED:
            if i == 'user':
                node['created'].update({i : remove_non_ascii(element.attrib[i])})
            else:
                node['created'].update({i : element.attrib[i]})
        node['pos'] = [str(float(element.attrib['lat'])), str(float(element.attrib['lon']))]
        #Iterates through all the child elements of the main element. 
        for child in element:
                #checks if the key is all lower case
                if lower.search(child.attrib['k']):
                    if child.attrib['k'] == 'phone':
                        #if it is a phone number it calls the clean_phone function
                        node[child.attrib['k']] = clean_phone(child.attrib['v'], True)
                    else:
                        node[child.attrib['k']] = child.attrib['v']
                #splits the key on the ':' char and checks if the len is 2. if greater than 2 we ignore it.
                elif len(child.attrib['k'].split(':')) == 2:
                    arr = child.attrib['k'].split(':')
                    if arr[0] == 'addr':
                        if 'address' not in node:
                            node['address'] = {}
                        if arr[1] == 'street':
                            #calls the update_name fuction which returns a cleaned up street address
                            node['address'].update({arr[1] : update_name(child.attrib['v'], mapping)})
                        elif arr[1] == 'state':
                            #For state, if takes the first 2 char of the word and returns them upper. ie FL
                            node['address'].update({arr[1] : child.attrib['v'][:2].upper()})
                        elif arr[1] == 'city':
                            #removes the problem charecters in the value.
                            node['address'].update({arr[1] : problemchars.sub("", child.attrib['v'])})
                        else:
                            node['address'].update({arr[1] : child.attrib['v']})
                    elif arr[0] == 'name':
                        None
                    else:
                        node[child.attrib['k'].split(':')[0]] = {child.attrib['k'].split(':')[1] : child.attrib['v']}
                elif problemchars.search(child.attrib['k']):
                    None
                else:
                    None
        return node
    #Most of the same logic is there for this type of element. 
    elif element.tag == 'way':
        node = {
            "id" : element.attrib['id'],
            "type": "way",
            "created" : {
                "changeset": None,
                "user": None,
                "version": None,
                "uid": None,
                "timestamp": None
            }
        }
        for i in CREATED:
            if i == 'user':
                node['created'].update({i : remove_non_ascii(element.attrib[i])})
            else:
                node['created'].update({i : element.attrib[i]})
        for child in element:
            if child.tag == 'nd':
                if 'node_refs' not in node:
                    node['node_refs'] = []
                node['node_refs'].append(child.attrib['ref'])
            else:
                if lower.search(child.attrib['k']):
                    if child.attrib['k'] == 'phone':
                        node[child.attrib['k']] = clean_phone(child.attrib['v'], True)
                    else:
                        node[child.attrib['k']] = child.attrib['v']
                elif len(child.attrib['k'].split(':')) == 2:
                    arr = child.attrib['k'].split(':')
                    if arr[0] == 'addr':
                        if 'address' not in node:
                            node['address'] = {}
                        if arr[1] == 'street':
                            node['address'].update({arr[1] : update_name(child.attrib['v'], mapping)})
                        elif arr[1] == 'state':
                            node['address'].update({arr[1] : child.attrib['v'][:2].upper()})
                        elif arr[1] == 'city':
                            node['address'].update({arr[1] : problemchars.sub("", child.attrib['v'])})
                        else:
                            node['address'].update({arr[1] : child.attrib['v']})
                    elif arr[0] == 'name':
                        None
                    else:
                        node[child.attrib['k'].split(':')[0]] = {child.attrib['k'].split(':')[1] : child.attrib['v']}
                elif problemchars.search(child.attrib['k']):
                    None
                else:
                    None
        return node
    else:
        return None

def process_map(file_in, pretty):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    number_to_process = 0
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return print("Your File has been proccessed and exported as DisneyWorld.osm.json")

process_map(FILE, False)
