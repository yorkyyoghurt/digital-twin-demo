import numpy as np

def compliance_matrix(inspiration_frames, expiration_frames, Pplat, PEEP):
    # functie om compliance matrix te maken
    
    delz = inspiration_frames - expiration_frames
    delp = Pplat - PEEP
    c = delz / delp
    return c #c is je compliance matrix

def collapse_berekenen(compliance_array):
    result = [
        [max(values) for values in zip(*rows)]
        for rows in zip(*compliance_array)
    ] # bereken de maximale compliance voor elke PEEP

    collapse_array = []
    collapse_percentage = []
    overdistention_array = []
    overdistention_percentage = []
    
    current_result_index = 0
    current_result_row = 0

    list_best_compliance = []

    

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
        collapse_percentage.append(np.mean(collapse_percent_matrix))
        overdistention_percentage.append(np.mean(overdistention_percent_matrix))
    
    return(collapse_array,overdistention_array, collapse_percentage, overdistention_percentage)

def calculate_optimal_peep(peep, collapse, overdistension):
    peep = np.asarray(peep, dtype=float)
    collapse = np.asarray(collapse, dtype=float)
    overdistension = np.asarray(overdistension, dtype=float)

    if not (len(peep) == len(collapse) == len(overdistension)):
        raise ValueError("All arrays must have the same length.")
    
    if len(peep) < 2:
        raise ValueError("At least two PEEP values are required.")
    
    difference = collapse - overdistension
    
    crossings = np.where(np.diff(np.sign(difference)) != 0)[0] # Find intervals where the difference changes sign

    if len(crossings) == 0:
        raise ValueError("The curves do not cross.")

    idx = crossings[0]
    
    # Values around the intersection
    x1, x2 = peep[idx], peep[idx + 1]
    y1, y2 = difference[idx], difference[idx + 1]
    
    # Linear interpolation to find the exact PEEP
    optimal_peep = x1 - y1 * (x2 - x1) / (y2 - y1)

    return optimal_peep