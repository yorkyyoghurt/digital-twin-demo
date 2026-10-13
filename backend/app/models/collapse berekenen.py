"""Maak collapse-overdistentie matrix vanuit complaince beelden"""
compliance_array = [[[1,1,1],[1,2,2],[1,2,3]],[[1,2,2],[1,2,2],[2,2,2]]]

def collapse_berekenen(compliance_array):
    result = [
        [max(values) for values in zip(*rows)]
        for rows in zip(*compliance_array)
    ] # bereken de maximale compliance voor elke PEEP

    collapse_array = []
    current_result_index = 0
    current_result_row = 0

    list_best_compliance = []

    overdistention_array = []

    for list in compliance_array:
        current_compliance = 0
        collapse_percent_matrix = []
        overdistention_percent_matrix = []
        for row in list: # bepaal de collapse van een rij van de matrix
            row_collapse = []
            row_overdistention = []
            for element in row:
                current_compliance = element

                best_compliance = result[current_result_row][current_result_index]
                current_result_index += 1
        
                collapse_percent = ((best_compliance-current_compliance)*100)/best_compliance
                overdistention_percent = collapse_percent

                if current_compliance == best_compliance: #bepaal of de beste compliance al is geweest
                    list_best_compliance.append((current_result_row,current_result_index))

                if (current_result_row,current_result_index) in list_best_compliance: # als de beste compliance al is geweest is de overdistention sws 0
                    overdistention_percent = 0

                if (current_result_row,current_result_index) not in list_best_compliance: # anders is de collapse sws 0
                                    collapse_percent = 0
                
                row_collapse.append(collapse_percent)
                row_overdistention.append(overdistention_percent)
                            
            collapse_percent_matrix.append(row_collapse)
            overdistention_percent_matrix.append(row_overdistention)
            current_result_index = 0
            current_result_row += 1
        current_result_row = 0

        overdistention_array.append(overdistention_percent_matrix)
        collapse_array.append(collapse_percent_matrix)
    
    return(collapse_array,overdistention_array)

overdistention_array, collapse_array = collapse_berekenen(compliance_array)




print(collapse_array)
print(overdistention_array)
        

