#!/usr/bin/python3
# iRule Builder
# Nicholas Schmidt
# 26 Jun 2021

# Command line parsing imports
import argparse

# Import System calls
import sys

# Dictionary replication tools
import copy

# YAML. Used for human inputs

import yaml
from ruamel.yaml import YAML
from ruamel.yaml import scanner

# JSON. Used for non-human inputs

import json

# Cerberus. Used to validate human and non-human inputs

from cerberus import Validator

# Templates. Basically the core to what we're doing here.

from jinja2 import Environment, FileSystemLoader

# Arguments Parsing
parser = argparse.ArgumentParser(description='Process YAML Inputs')
parser.add_argument('-v', '--verbosity', action='count', default=0, help='Output Verbosity')
parser.add_argument('-g', '--generate', action='store_true', help='Generate a device file to customize.')
parser.add_argument('-o', '--output', help='Output file')
parser.add_argument('-i', '--input', help='Input. Pass this a YAML file')
args = parser.parse_args()

# Generate a file for a user to build on
if(args.generate):
    try:
        with open("schema/irule.json", 'r') as json_file:
            example_dict = json.loads(json_file.read())
    except Exception as e:
        sys.exit("E1200: JSON Load failure: " + str(e))
    # First, let's take the imported dictionary and populate it full of stuff
    populated_dict = copy.deepcopy(example_dict)
    populated_dict.pop('type', None)
    schema_validator = Validator(example_dict, require_all=True)

    # Then, let's turn the output into a string
    output_output = yaml.dump(populated_dict)
    print(output_output)

    # Optionally Write all that to a file
    if(args.output):
        try:
            filehandle = open(args.output, "w")
            filehandle.write(output_output)
            filehandle.close()
        except Exception as e:
            sys.exit("E1500: Error writing to file! " + str(e))
    sys.exit()
elif(args.input):
    # Load Templates folder as Jinja2 root
    local_env = Environment(loader=FileSystemLoader('templates'))

    # Load Definition Classes
    yaml_input = YAML(typ='safe')
    yaml_dict = {}

    # Input can take a file first, but will fall back to YAML processing of a string
    try:
        yaml_dict = yaml_input.load(open(args.input, 'r'))
    except FileNotFoundError:
        print('I2000: Not found as file, trying as a string...')
        yaml_dict = yaml_input.load(args.input)
    except scanner.ScannerError as exc:
        # Test for malformatted yaml
        print('E1001: YAML Parsing error!')
        if (args.verbosity > 0):
            print(exc)
    except Exception as exc:
        # Fallback error dump
        print('E9999: An unknown error has occurred!')
        if (args.verbosity > 0):
            print(exc)
            print(type(exc))
            print(exc.args)
    else:
        if args.verbosity > 0:
            print(json.dumps(yaml_dict, indent=4))
            print("Valid YAML Found! Executing Template Actions...")

    # Validate YAML Structure (body)
    try:
        with open("schema/irule.json", 'r') as json_file:
            validation_dict = json.loads(json_file.read())
    except Exception as e:
        sys.exit("E1300: Schema processing issue: " + str(e))
    else:
        schema_validator = Validator(validation_dict, require_all=True)
        if not (schema_validator.validate(yaml_dict)):
            # Provide intuitive errors on why it failed validation, pretty printed
            sys.exit("E1400: Validation Errors found:\n" + json.dumps(schema_validator.errors, indent=4))

    # Set Templates and Validators now that we know what to validate against

    try:
        device_template = local_env.get_template('irule.j2')
    except Exception as e:
        sys.exit('E1101: Device template not found! Could not find key ' + str(e))

    # Do stuff with the data!

    # Generate Overall Configuration file
    output_output = ""
    output_output += device_template.render(yaml_dict)
    output_output += "\n"

    # Write all that to a file
    if(args.output):
        try:
            filehandle = open(args.output, "w")
            filehandle.write(output_output)
            filehandle.close()
        except Exception as e:
            sys.exit("Error writing to file! " + str(e))
    else:
        print(output_output)
