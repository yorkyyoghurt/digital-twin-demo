#input dictionary, voltage vanuit EIT, PEEP & p_plateau vanuit ventilator
input_dictionary = {"voltage_meting":0 , "PEEP":0 , "p_plateau":0 , "mesh":0}
#Deze waardes moeten van patient tot patient aangepast worden
#Het zijn ook niet allemaal enkele getallen, maar het type data kan ook aangepast worden

#variabel dictionary, als iedereen hier zijn gebruikte variabelen inzet blijft alles centraal
variabel_dictionary = {"compliance_array":[[[1,1,1],[1,2,2],[1,2,3]],[[1,2,2],[1,2,2],[2,2,2]]] , 
                       }

#output dictionary, zodra we iets van informatie hebben uit de code kan het hier in gezet worden
output_dictionary = {}
