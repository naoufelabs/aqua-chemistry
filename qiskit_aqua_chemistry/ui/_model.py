# -*- coding: utf-8 -*-

# Copyright 2018 IBM.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

import os
import json
from qiskit_aqua_chemistry import AquaChemistryError
from qiskit_aqua_chemistry.drivers import ConfigurationManager
from qiskit_aqua_chemistry.parser import InputParser
from qiskit_aqua.parser import JSONSchema
from qiskit_aqua import local_pluggables
from qiskit_aqua_chemistry.core import local_chemistry_operators
from qiskit_aqua_chemistry.ui._uipreferences import UIPreferences

class Model(object):
   
    def __init__(self):
        """Create Model object."""
        self._configuration_mgr = ConfigurationManager()
        self._parser = InputParser()
        
    def is_empty(self):
        return self._parser is None or len(self._parser.get_section_names()) == 0
    
    def new(self):
        try:
            dict = {}
            jsonfile = os.path.join(os.path.dirname(__file__), 'input_template.json')
            with open(jsonfile) as json_file:
                dict = json.load(json_file)
                
            self._parser = InputParser(dict)
            self._parser.parse()
            uipreferences = UIPreferences()
            if uipreferences.get_populate_defaults(True):
                self._parser.validate_merge_defaults()
                self._parser.commit_changes()
                
            return self._parser.get_section_names()   
        except:
            self._parser = None
            raise
        
    def load_file(self,filename):
        if filename is None:
            return []
        try:
            self._parser = InputParser(filename)
            self._parser.parse()
            uipreferences = UIPreferences()
            if uipreferences.get_populate_defaults(True):
                self._parser.validate_merge_defaults()
                self._parser.commit_changes()
                
            return self._parser.get_section_names()   
        except:
            self._parser = None
            raise
            
    def get_filename(self):
        if self._parser is None:
            return None
    
        return self._parser.get_filename()
            
    def is_modified(self):
        if self._parser is None:
            return False
                
        return self._parser.is_modified()
        
    def save_to_file(self,filename):
        if self.is_empty():
            raise AquaChemistryError("Empty input data.")
                
        self._parser.save_to_file(filename) 
        
        
    def get_dictionary(self):
        if self.is_empty():
            raise AquaChemistryError("Empty input data.")
            
        return self._parser.to_dictionary()
        
    def export_dictionary(self,filename):
        if self.is_empty():
            raise AquaChemistryError("Empty input data.")
                
        self._parser.export_dictionary(filename) 
            
    def get_section_names(self):
        if self._parser is None:
            return []
        
        return self._parser.get_section_names()
    
    def get_property_default_values(self,section_name,property_name):
        if self._parser is None:
            return None
        
        return self._parser.get_property_default_values(section_name,property_name)
    
    def section_is_text(self,section_name):
        if self._parser is None:
            return False
        
        return self._parser.section_is_text(section_name)
    
    def get_section_text(self,section_name):
        if self._parser is None:
            return ''
        
        return self._parser.get_section_text(section_name)
    
    def get_section_data(self,section_name):
        if self._parser is None:
            return None
        
        return self._parser.get_section_data(section_name)
     
    def get_section_properties(self,section_name):
        if self._parser is None:
            return {}
        
        return self._parser.get_section_properties(section_name)
    
    def get_section_properties_with_substitution(self,section_name):
        properties = self.get_section_properties(section_name)
        result_tuples  = self._parser.check_if_substitution_key(section_name,list(properties.keys()))
        properties_with_substitution = {}
        for result_tuple in result_tuples:
            properties_with_substitution[result_tuple[0]] = (properties[result_tuple[0]],result_tuple[1])
            
        return properties_with_substitution
    
    def default_properties_equals_properties(self,section_name):
        if self.section_is_text(section_name): 
            return self.get_section_default_properties(section_name) == self.get_section_data(section_name)
        
        default_properties = self.get_section_default_properties(section_name)
        properties = self.get_section_properties(section_name)
        if not isinstance(default_properties,dict) or not isinstance(properties,dict):
            return default_properties == properties
            
        if JSONSchema.NAME in properties:
            default_properties[JSONSchema.NAME] = properties[JSONSchema.NAME]
            
        if len(default_properties) != len(properties):
            return False
         
        substitution_tuples  = self._parser.check_if_substitution_key(section_name,list(properties.keys()))
        for substitution_tuple in substitution_tuples:
            property_name = substitution_tuple[0]
            if property_name not in default_properties:
                return False
            
            if not substitution_tuple[1]:
                if default_properties[property_name] != properties[property_name]:
                    return False
                
        return True
     
    def get_section_property(self,section_name,property_name):
        if self._parser is None:
            return None
        
        return self._parser.get_section_property(section_name,property_name)
    
    def get_section(self,section_name):
        return self._parser.get_section(section_name) if self._parser is not None else None
    
    def set_section(self,section_name):
        if self._parser is None:
            raise AquaChemistryError('Input not initialized.')
            
        self._parser.set_section(section_name)
        value = self._parser.get_section_default_properties(section_name)
        if isinstance(value,dict):
            for property_name,property_value in value.items():
                self._parser.set_section_property(section_name,property_name,property_value)
                
            # do one more time in case schema was updated
            value = self._parser.get_section_default_properties(section_name)
            for property_name,property_value in value.items():
                self._parser.set_section_property(section_name,property_name,property_value)             
        else:
            if value is None:
                types = self._parser.get_section_types(section_name)
                if 'null' not in types:
                    if 'string' in types:
                        value = ''
                    elif 'object' in types:
                        value = {}
                    elif 'array' in types:
                        value = []
                
            self._parser.set_section_data(section_name,value)
            
    def set_default_properties_for_name(self,section_name):
        if self._parser is None:
            raise AquaChemistryError('Input not initialized.')
            
        name = self._parser.get_section_property(section_name,JSONSchema.NAME)
        self._parser.delete_section_properties(section_name)
        if name is not None:
            self._parser.set_section_property(section_name,JSONSchema.NAME,name)
            
        value = self._parser.get_section_default_properties(section_name)
        if isinstance(value,dict):
            for property_name,property_value in value.items():
                if property_name != JSONSchema.NAME:
                    self._parser.set_section_property(section_name,property_name,property_value)
        else:
            if value is None:
                types = self._parser.get_section_types(section_name)
                if 'null' not in types:
                    if 'string' in types:
                        value = ''
                    elif 'object' in types:
                        value = {}
                    elif 'array' in types:
                        value = []
                
            self._parser.set_section_data(section_name,value)
            
    @staticmethod
    def is_pluggable_section(section_name):
        return InputParser.is_pluggable_section(section_name)
    
    def get_operator_section_names(self):
        problem_name = None
        if self._parser is not None:
            problem_name = self.get_section_property(JSONSchema.PROBLEM,JSONSchema.NAME)
        if problem_name is None:
            problem_name = self.get_property_default_value(JSONSchema.PROBLEM,JSONSchema.NAME)
                
        if problem_name is None:
            return local_chemistry_operators()
            
        operator_names = []
        for operator_name in local_chemistry_operators():
            problems = InputParser.get_operator_problems(operator_name)
            if problem_name in problems:
                operator_names.append(operator_name)
            
        return operator_names
    
    def get_pluggable_section_names(self,section_name):
        if not Model.is_pluggable_section(section_name):
            return []
        
        if JSONSchema.ALGORITHM == section_name:
            problem_name = None
            if self._parser is not None:
                problem_name = self.get_section_property(JSONSchema.PROBLEM,JSONSchema.NAME)
            if problem_name is None:
                problem_name = self.get_property_default_value(JSONSchema.PROBLEM,JSONSchema.NAME)
                    
            if problem_name is None:
                return local_pluggables(JSONSchema.ALGORITHM)
           
            algo_names = []
            for algo_name in local_pluggables(JSONSchema.ALGORITHM):
                problems = InputParser.get_algorithm_problems(algo_name)
                if problem_name in problems:
                    algo_names.append(algo_name)
                
            return algo_names
        
        return local_pluggables(section_name)
             
    def delete_section(self, section_name):
        if self._parser is None:
            raise AquaChemistryError('Input not initialized.')
            
        self._parser.delete_section(section_name)
        
    def get_default_sections(self):
        if self._parser is None:
            raise AquaChemistryError('Input not initialized.')
            
        return self._parser.get_default_sections()
         
    def get_section_default_properties(self,section_name):
        if self._parser is None:
            raise AquaChemistryError('Input not initialized.')
            
        return self._parser.get_section_default_properties(section_name)
    
    def allows_additional_properties(self,section_name):
        if self._parser is None:
            raise AquaChemistryError('Input not initialized.')
        
        return self._parser.allows_additional_properties(section_name)
    
    def get_property_default_value(self,section_name,property_name):
        if self._parser is None:
            raise AquaChemistryError('Input not initialized.')
            
        return self._parser.get_property_default_value(section_name,property_name)
    
    def get_property_types(self,section_name,property_name):
        if self._parser is None:
            raise AquaChemistryError('Input not initialized.')
            
        return self._parser.get_property_types(section_name,property_name)
    
    def set_section_property(self, section_name, property_name, value):
        if self._parser is None:
            raise AquaChemistryError('Input not initialized.')
            
        self._parser.set_section_property(section_name,property_name,value)
        if InputParser.is_pluggable_section(section_name) and property_name == JSONSchema.NAME:
            properties = self._parser.get_section_default_properties(section_name)
            if isinstance(properties,dict):
                properties[ JSONSchema.NAME] = value
                self._parser.delete_section_properties(section_name)
                for property_name,property_value in properties.items():  
                    self._parser.set_section_property(section_name,property_name,property_value)
        
    def delete_section_property(self, section_name, property_name):
        if self._parser is None:
            raise AquaChemistryError('Input not initialized.')
            
        self._parser.delete_section_property(section_name, property_name)
        if InputParser.is_pluggable_section(section_name) and property_name == JSONSchema.NAME:
            self._parser.delete_section_properties(section_name)
            
    def set_section_text(self, section_name, value):  
        if self._parser is None:
            raise AquaChemistryError('Input not initialized.')
            
        self._parser.set_section_data(section_name, value)
        
    def delete_section_text(self, section_name):  
        if self._parser is None:
            raise AquaChemistryError('Input not initialized.')
            
        self._parser.delete_section_text(section_name)
