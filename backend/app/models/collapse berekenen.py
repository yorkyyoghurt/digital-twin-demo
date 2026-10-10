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

    for list in compliance_array:
        current_compliance = 0
        collapse_percent_matrix = []
        for row in list: # bepaal de collapse van een rij van de matrix
            row_collapse = []
            for element in row:
                current_compliance = element

                best_compliance = result[current_result_row][current_result_index]
                print(best_compliance)
                current_result_index += 1
        
                collapse_percent = ((best_compliance-current_compliance)*100)/best_compliance
                row_collapse.append(collapse_percent)
                            
            collapse_percent_matrix.append(row_collapse)
            current_result_index = 0
            current_result_row += 1
        current_result_row = 0

        collapse_array.append(collapse_percent_matrix)

    print(result)
    
    return(collapse_array)

collapse_array = collapse_berekenen(compliance_array)




print(collapse_array)
        

