# importing formatting packages
import re
import os
import json
import pandas as pd
import numpy as np
import xlsxwriter
import copy
import ctypes



def getInputJson(json_path):
    with open(json_path, 'r+') as f:
        text = f.read()
        text = re.sub('[0-9]{2}_', '', text)
        f.seek(0)
        f.write(text)
        f.truncate()
    with open(json_path) as file:
        data = json.load(file)

    return data


def normalizeJson(data):

    nodes = pd.json_normalize(data, 'nodes')

    nodes.rename(columns=lambda x: x.replace('data.', ''), inplace=True)
    nodes.rename(columns=lambda x: x.replace('properties.', ''), inplace=True)
    nodes.rename(columns=lambda x: x.replace('attributes.', ''), inplace=True)
    nodes.drop(['x', 'y', 'color', 'radius', 'shape'], axis=1, inplace=True)

    edges = pd.json_normalize(data, 'edges')
    edges.rename(columns=lambda x: x.replace('data.', ''), inplace=True)
    edges.rename(columns={'properties.Source': 'Data Source'}, inplace=True)
    edges.rename(columns=lambda x: x.replace('properties.', ''), inplace=True)
    edges.rename(columns=lambda x: x.replace('attributes.', ''), inplace=True)
    edges.drop(['color', 'width'], axis=1, inplace=True)

    nodes = nodes.replace(np.nan, 'NA', regex=True)
    edges = edges.replace(np.nan, 'NA', regex=True)
    #nodes = nodes.astype(str)
    #edges = edges.astype(str)

    return nodes, edges

def getAvailableSeed(nodes):

    ava_seed_node = nodes[['PAN', 'Name']].loc[nodes['PAN'] != 'NA']
    ava_seed_node.rename(columns={"Name": "PAN Name"}, inplace=True)
    return ava_seed_node


def flattenData(nodes, edges):
    nodes['source'] = nodes['id']
    nodes['target'] = nodes['id']

    """"related_nodes = nodes[['id', 'Name', 'categories', 'Pincode', 'Financial Year',
                           'Pan Allotment Date', 'Person Of Interest flags',
                           'Last AY for which ITR filed', 'Income Range', 'Income Tax Ward/Circle',
                           'Turnover Range', 'Mobile Number', 'Date Of Birth/Incorporation',
                           'Address', 'Pincode Category', 'Nature Of Business', 'Email', 'PAN',
                           'Gender', 'latitude', 'longitude', 'Other Income Category']]

    related_links = edges.merge(nodes[['source', 'Name', 'PAN']], on='source', how='left')
    related_links.rename(columns={"Name": "Source-Name", "PAN": "Source-PAN"}, inplace=True)
    related_links = related_links.merge(nodes[['target', 'Name', 'PAN']], on='target', how='left')
    related_links.rename(columns={"Name": "Target-Name", "PAN": "Target-PAN"}, inplace=True)

    related_links = related_links[
        ['id', 'source', 'Source-Name', 'Source-PAN', 'target', 'Target-Name', 'Target-PAN', 'text', 'type',
         'Financial Year', 'Tax',
         'Transaction Amount']]

    return related_nodes, related_links"""

#Function for auto-fitting the column width

def get_col_widths2(related_nodes):
    # First we find the maximum length of the index column
    idx_max = max([len(str(s)) for s in related_nodes.index.values] + [len(str(related_nodes.index.name))])
    # Then, we concatenate this to the max of the lengths of column name and its values for each column, left to right
    return [idx_max] + [max([len(str(s)) for s in related_nodes[col].values] + [len(col)]) for col in related_nodes.columns]

# Function for auto-fitting the column width

def get_col_widths(related_links):
        # First we find the maximum length of the index column
        idx_max = max([len(str(s)) for s in related_links.index.values] + [len(str(related_links.index.name))])
        # Then, we concatenate this to the max of the lengths of column name and its values for each column, left to right
        return [idx_max] + [max([len(str(s)) for s in related_links[col].values] + [len(col)]) for col in
                            related_links.columns]

def generateXLS(seed_pan, module, nodes, edges,img_path):

    related_nodes = copy.deepcopy(nodes)
    #pdb.set_trace()
    #print(seed_pan)
    seed_node = nodes[['PAN', 'Name']].loc[nodes['Name'] == seed_pan]
    seed_node.rename(columns={"Name": "PAN Name"}, inplace=True)
    #print(seed_node)

    # Converting all date columns to Datetime format
    related_nodes[[col for col in related_nodes.columns if "Date" in col]] = related_nodes[
        [col for col in related_nodes.columns if "Date" in col]].apply(pd.to_datetime, format='%d-%b-%Y',
                                                                       errors='coerce')
    edges[[col for col in edges.columns if "Date" in col]] = edges[[col for col in edges.columns if "Date" in col]] = \
    edges[[col for col in edges.columns if "Date" in col]].apply(pd.to_datetime, format='%d%b%Y:%H:%M:%S',
                                                                 errors='coerce')

    if "TDS" in module:
        related_links = edges.merge(nodes[['source', 'text', 'PAN', 'TAN']], on='source', how='left')
        related_links.rename(columns={"text_y": "Source-Name", "PAN": "Source-PAN", 'TAN': "Source-TAN"}, inplace=True)
        related_links = related_links.merge(nodes[['target', 'text', 'PAN', 'TAN']], on='target', how='left')
        related_links.rename(columns={"text": "Target-Name", "PAN": "Target-PAN", 'TAN': "Target-TAN"}, inplace=True)
        #print("TDS")
    else:
        related_links = edges.merge(nodes[['source', 'Name', 'PAN']], on='source', how='left')
        related_links.rename(columns={"Name": "Source-Name", "PAN": "Source-PAN"}, inplace=True)
        related_links = related_links.merge(nodes[['target', 'Name', 'PAN']], on='target', how='left')
        related_links.rename(columns={"Name": "Target-Name", "PAN": "Target-PAN"}, inplace=True)
        #print('No TDS')

    #print(related_links)

    # Merging additional info columns into one column for Relation module
    if "Relation" in module:
        cols = [col for col in related_links.columns if "Additional" in col]
        related_links['Additional Relationships Info'] = related_links[cols].apply(
            lambda row: ', '.join(row.values.astype(str)), axis=1)
        related_links['Additional Relationships Info'] = related_links['Additional Relationships Info'].str.replace(
            "NA,", "")
        related_links.drop(cols, axis=1, inplace=True)
    else:
        pass
    #print(related_links)

    # Re-ordering the columns
    if "TDS" in module:
        cols_to_order = ['Source-Name', 'Source-PAN', 'Source-TAN', 'Target-Name', 'Target-PAN', 'Target-TAN']
        new_columns = cols_to_order + (related_links.columns.drop(cols_to_order).tolist())
        related_links = related_links[new_columns]
    elif "Relation" in module:
        cols_to_order = ['Source-Name', 'Source-PAN', 'Target-Name', 'Target-PAN']
        new_columns = cols_to_order + (related_links.columns.drop(cols_to_order).tolist())
        related_links = related_links[new_columns]
    else:
        cols_to_order = ['Target-Name', 'Target-PAN', 'Source-Name', 'Source-PAN']
        new_columns = cols_to_order + (related_links.columns.drop(cols_to_order).tolist())
        related_links = related_links[new_columns]
    #print(related_links)

    cols_to_order_nodes = ['Name', 'text', 'PAN', 'Pincode', 'Pincode Category', 'Address', 'Mobile Number', 'Email']
    new_columns_nodes = cols_to_order_nodes + (related_nodes.columns.drop(cols_to_order_nodes).tolist())
    related_nodes = related_nodes[new_columns_nodes]
    #print(related_nodes)

    if "TDS" in module:
        related_links.rename(
            columns={'Source-PAN': 'Deductee PAN', 'Target-PAN': 'Deductor PAN', 'Source-Name': 'Deductee Name',
                     'Target-Name': 'Deductor Name', 'Target-TAN': 'Deductor TAN', 'Source-TAN': 'Deductee TAN',
                     'type': 'TDS Type'}, inplace=True)
        related_links['TDS Type'] = related_links['TDS Type'].str.replace(u"Â", "")
        related_links['Deductee Name'], related_links['Deductor Name'] = np.where(
            related_links['TDS Type'].astype(str).str.contains('receiver') == True,
            (related_links['Deductor Name'], related_links['Deductee Name']),
            (related_links['Deductee Name'], related_links['Deductor Name']))
        related_links['Deductee PAN'], related_links['Deductor PAN'] = np.where(
            related_links['TDS Type'].astype(str).str.contains('receiver') == True,
            (related_links['Deductor PAN'], related_links['Deductee PAN']),
            (related_links['Deductee PAN'], related_links['Deductor PAN']))
        related_links.drop(['id', 'source', 'target', 'text_x', 'Financial Year', 'Deductee TAN'], axis=1, inplace=True)
        related_links['Amount Of Transaction'] = related_links['Amount Of Transaction'].map('{:,.0f}'.format)
        related_links['TDS Deducted'] = related_links['TDS Deducted'].map('{:,.0f}'.format)
    elif "Share" in module:
        related_links.rename(
            columns={'Source-PAN': 'Entity PAN', 'Target-PAN': 'Shareholder PAN', 'Source-Name': 'Entity Name',
                     'Target-Name': 'Shareholder Name'}, inplace=True)
        related_links.drop(['id', 'source', 'target', 'text', 'type', 'Financial Year'], axis=1, inplace=True)

    elif "Relation" in module:
        related_links.rename(
            columns={'Source-PAN': 'Seed Node PAN', 'Target-PAN': 'Related Entity PAN', 'Source-Name': 'Seed Node Name',
                     'Target-Name': 'Related Entity Name', 'type': 'Relationship Type'}, inplace=True)
        related_links.drop(['id', 'source', 'target', 'text', 'Financial Year', 'EDGE_ID', 'Relationship Score',
                            'PRIMARY_RELATIONSHIP'], axis=1, inplace=True)

    else:
        related_links.rename(
            columns={'Source-PAN': 'Seller PAN', 'Target-PAN': 'Purchaser PAN', 'Source-Name': 'Seller Name',
                     'Target-Name': 'Purchaser Name'}, inplace=True)
        related_links.drop(['id', 'source', 'target', 'text', 'type', 'Financial Year'], axis=1, inplace=True)
        related_links['Transaction Amount'] = related_links['Transaction Amount'].map('{:,.0f}'.format)
        related_links['Tax'] = related_links['Tax'].map('{:,.0f}'.format)




    Financial_Year = related_nodes.iloc[0]['Financial Year']


    if "TDS" in module:
        related_nodes.drop(['id', 'source', 'target', 'Name', 'Financial Year'], axis=1, inplace=True)
        related_nodes.rename(columns={'categories': 'Categories', "text": "Name"}, inplace=True)

    else:
        related_nodes.rename(columns={'categories': 'Categories'}, inplace=True)
        related_nodes.drop(['id', 'source', 'target', 'text', 'Financial Year'], axis=1, inplace=True)

    # POI Nodes
    POI_Nodes = related_nodes.loc[
        related_nodes['Categories'].apply(str).str.contains('Person Of Interest')].reset_index(drop=True)
    POI_Nodes['Risk Flags'] = POI_Nodes['Person Of Interest flags'].apply(lambda x: len(x.split(',')))
    POI_Nodes = POI_Nodes[['PAN', 'Name', 'Risk Flags', 'Person Of Interest flags']]

    # Red flags segregation
    POI_red_flags = POI_Nodes[['Name', 'PAN', 'Person Of Interest flags']]
    POI_red_flags.rename(columns={'Person Of Interest flags': 'Risk_Flag'}, inplace=True)
    POI_red_flags = POI_red_flags.assign(Risk_Flag=POI_red_flags['Risk_Flag'].str.split(',')).explode(
        'Risk_Flag').reset_index(drop=True)
    POI_red_flags = POI_red_flags[['PAN', 'Name', 'Risk_Flag']]

    # POI Relationships
    if "TDS" in module:
        POI_related_links = related_links.loc[(related_links['Deductee PAN'].isin(POI_red_flags['PAN'])) | (
            related_links['Deductor PAN'].isin(POI_red_flags['PAN']))].reset_index(drop=True)
        POI_related_links.drop(['Deductor PAN'], axis=1, inplace=True)
        related_links.drop(['Deductor PAN'], axis=1, inplace=True)
    elif "Share" in module:
        POI_related_links = related_links.loc[(related_links['Shareholder PAN'].isin(POI_red_flags['PAN'])) | (
            related_links['Entity PAN'].isin(POI_red_flags['PAN']))].reset_index(drop=True)
    elif "Relation" in module:
        POI_related_links = related_links.loc[(related_links['Related Entity PAN'].isin(POI_red_flags['PAN'])) | (
            related_links['Seed Node PAN'].isin(POI_red_flags['PAN']))].reset_index(drop=True)
    else:
        POI_related_links = related_links.loc[(related_links['Purchaser PAN'].isin(POI_red_flags['PAN'])) | (
            related_links['Seller PAN'].isin(POI_red_flags['PAN']))].reset_index(drop=True)



    writer = pd.ExcelWriter(r'./Link_Analysis_'+module+'_'+seed_node.iloc[0]['PAN']+'.xlsx', engine='xlsxwriter')

    len1 = len(seed_node) + 20

    # len2 = len(seed_node) + len(related_nodes)+24

    # Write all nodes and edges data to an excel
    # seed_node.to_excel(writer, sheet_name=module, startrow=2, index=False, header=False)
    related_links.to_excel(writer, sheet_name='All Relationships', startrow=len1, index=False)
    related_nodes.to_excel(writer, sheet_name='All Nodes', startrow=2, index=False)

    # Write Person of Interest data to an excel
    POI_Nodes.to_excel(writer, sheet_name='Person of Interest', startrow=2, index=False)
    POI_red_flags.to_excel(writer, sheet_name='Person of Interest', startrow=len(POI_Nodes) + 5, index=False)
    POI_related_links.to_excel(writer, sheet_name='Person of Interest',
                               startrow=len(POI_Nodes) + len(POI_red_flags) + 8, index=False)

    # Get workbook
    workbook = writer.book

    title_format = workbook.add_format({
        'bold': False,
        'valign': 'top',
        'fg_color': '#F1FF7C',
        'border': 1})

    # Get Sheet1
    worksheet = writer.sheets['All Relationships']
    worksheet_nodes = writer.sheets['All Nodes']
    worksheet_POI = writer.sheets['Person of Interest']
    # worksheet.hide_gridlines(2)

    # worksheet.write(0,0, 'Seed Node',title_format)
    merge_format = workbook.add_format({
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'yellow'})

    worksheet.merge_range(0, 0, 0, 5,
                          module + ' Analysis for ' + seed_node.iloc[0]['PAN Name'] + " (" + seed_node.iloc[0][
                              'PAN'] + ") for FY " + Financial_Year, merge_format)
    worksheet_nodes.merge_range(0, 0, 0, 1, module + ' - All Nodes', merge_format)
    worksheet_POI.merge_range(0, 0, 0, 2, 'Person of Interest Analysis for ' + seed_node.iloc[0]['PAN Name'] + " (" +
                              seed_node.iloc[0]['PAN'] + ")", merge_format)

    worksheet.insert_image(1 + 1, 1, img_path,
                           {'x_scale': 0.46, 'y_scale': 0.46, 'object_position': 3})

    worksheet.merge_range(len1 - 1, 0, len1 - 1, 2, module + ' - All Relationships', merge_format)
    worksheet_POI.merge_range(len(POI_Nodes) + 4, 0, len(POI_Nodes) + 4, 1, 'Person of Interest Flags', merge_format)
    worksheet_POI.merge_range(len(POI_Nodes) + len(POI_red_flags) + 7, 0, len(POI_Nodes) + len(POI_red_flags) + 7, 1,
                              'Relationships ', merge_format)

    # Add a header format.
    header_format = workbook.add_format({
        'bold': False,
        'valign': 'left',
        'fg_color': '#d9e1f2',
        'border': 1})

    # Write the column headers with the defined format.
    for col_num, value in enumerate(related_links.columns.values):
        worksheet.write(len1, col_num, value, header_format)

    for col_num, value in enumerate(related_nodes.columns.values):
        worksheet_nodes.write(2, col_num, value, header_format)

    for col_num, value in enumerate(POI_Nodes.columns.values):
        worksheet_POI.write(2, col_num, value, header_format)

    for col_num, value in enumerate(POI_red_flags.columns.values):
        worksheet_POI.write(len(POI_Nodes) + 5, col_num, value, header_format)

    for col_num, value in enumerate(POI_related_links.columns.values):
        worksheet_POI.write(len(POI_Nodes) + len(POI_red_flags) + 8, col_num, value, header_format)

    # Applying function to auto-fit the width of columns
    for i, width in enumerate(get_col_widths(related_links)):
        worksheet.set_column(i, i, width)
    for i, width in enumerate(get_col_widths(related_nodes)):
        worksheet_nodes.set_column(i, i, width)
    for i, width in enumerate(get_col_widths(POI_red_flags)):
        worksheet_POI.set_column(i, i, width)

    writer.save()
    writer.close()
    return True



def main():
    modules = ["Relationship", "TDS Payments", "GST Payments", "Shareholding Details"]
    data = getInputJson("sandbox.json")
    nodes, edges = normalizeJson(data)
    seed_list = getAvailableSeed(nodes)
    #print(seed_list)
    #flattenData(nodes, edges)


if __name__ == "__main__":
    main()

