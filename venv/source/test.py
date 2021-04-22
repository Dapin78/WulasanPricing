import pandas as pd
import streamlit as st

# Import the data

costPerLiter = pd.read_csv(r"C:\Users\Alexandre Pineau\PycharmProjects\WulasanPricing\data\CSVCostPerLiter.csv", decimal = ',', delimiter = ";")
costPerUnit = pd.read_csv(r"C:\Users\Alexandre Pineau\PycharmProjects\WulasanPricing\data\CSVCostPerUnit.csv", decimal = ',', delimiter = ";")
pricePerLiter = pd.read_csv(r"C:\Users\Alexandre Pineau\PycharmProjects\WulasanPricing\data\CSVPricePerLiter.csv", decimal = ',', delimiter = ";")
pricePerUnit = pd.read_csv(r"C:\Users\Alexandre Pineau\PycharmProjects\WulasanPricing\data\CSVPricePerUnit.csv", decimal = ',', delimiter = ";")
nbBottles = pd.read_csv(r"C:\Users\Alexandre Pineau\PycharmProjects\WulasanPricing\data\NbBottles.csv", decimal = ',', delimiter = ";")
marginDefinition = pd.read_csv(r"C:\Users\Alexandre Pineau\PycharmProjects\WulasanPricing\data\CSVMarginDefinition.csv", decimal = ',', delimiter = ";")

class Item:
    def __init__(self, reference, bottleSize, conditionning):
        self.reference = reference
        self.bottleSize = bottleSize
        self.conditionning = conditionning

        self.standardCosts = self.standard_costs()
        self.standardPrices = self.standard_prices()
        self.bottlesPerPackage = self.number_of_bottles()


    def standard_costs(self):
        literCost = costPerLiter[(costPerLiter['Product'] == self.reference) & (costPerLiter['Unit Conditionning'] == self.bottleSize)].loc[:, self.conditionning]
        unitCost = costPerUnit[(costPerUnit['Product'] == self.reference) & (costPerUnit['Unit Conditionning'] == self.bottleSize)].loc[:, self.conditionning]
        return literCost, unitCost

    def standard_prices(self):
        literPrice = pricePerLiter[(pricePerLiter['Product'] == self.reference) & (pricePerLiter['Unit Conditionning'] == self.bottleSize)].loc[:, self.conditionning]
        unitPrice = pricePerUnit[(pricePerUnit['Product'] == self.reference) & (pricePerUnit['Unit Conditionning'] == self.bottleSize)].loc[:, self.conditionning]
        return literPrice, unitPrice

    def number_of_bottles(self):
        listCond = self.conditionning.split(sep= ' ')
        if listCond[1] == '1/2':
            listCond[1] = '0.5'
        listCond[1] = float(listCond[1])
        if listCond[2] == 'Paletten':
            listCond[2] = 'Palette'

        if listCond[2] == 'Palette':
            bottlesPerPackage = nbBottles[nbBottles['Bottle Size'] == self.bottleSize].loc[:, listCond[2]].values * listCond[1]
        elif listCond[2] == 'Kartons':
            bottlesPerPackage = nbBottles[nbBottles['Bottle Size'] == self.bottleSize].loc[:, listCond[2]].values * listCond[1]

        return bottlesPerPackage

class Customer:
    def __init__(self, type, potential):
        self.type = type
        self.potential = potential
        self.margins = self.define_margins()

    def define_margins(self):

        minMargin = marginDefinition[(marginDefinition['Customer Potential'] == self.potential) &
                                     (marginDefinition['Customer Type'] == self.type) &
                                     (marginDefinition['Margin Type'] == 'Min')
                                     ]

        maxMargin = marginDefinition[(marginDefinition['Customer Potential'] == self.potential) &
                                     (marginDefinition['Customer Type'] == self.type) &
                                     (marginDefinition['Margin Type'] == 'Max')
                                     ]

        return minMargin, maxMargin

class Request:
    def __init__(self, quantity, item, customer):
        self.quantity = quantity
        self.item = item
        self.customer = customer

        self.margins = self.set_margins()
        self.unitPrices = self.set_unit_prices()
        self.nbBottles = self.item.bottlesPerPackage * quantity

    def set_unit_prices(self):
        if (type(self.item) == Item) & (type(self.customer) == Customer):
            minPrice = (1 + self.margins[0].values) * self.item.standardCosts[1].values
            maxPrice = (1 + self.margins[1].values) * self.item.standardCosts[1].values
        return minPrice, maxPrice

    def set_margins(self):
        listMOQ = [20, 50, 200, 500, 1000, 2000, 5000]
        i = 0
        while self.quantity > listMOQ[i]:
            i += 1
        column = listMOQ[i - 1]

        minMargin = self.customer.margins[0].loc[:, str(column)]
        maxMargin = self.customer.margins[1].loc[:, str(column)]

        return minMargin, maxMargin



st.title('WULASAN Pricing Application')

st.sidebar.title('Input for Calculation')

st.sidebar.header('Customer information')
st.sidebar.write('Give details about the customer making the request')
customerType = st.sidebar.selectbox(
    'Specify the typology of the customer:',
    ['Reseller', 'B2B']
)

customerPotential = st.sidebar.select_slider(
    'What is the potential future value of this customer?',
    [1,2,3,4,5],
    3
)

st.sidebar.header('Request details')
st.sidebar.write('Specify the needed information about the customer\'s request.')

product = st.sidebar.selectbox(
    'Which product needs to be priced?',
    costPerLiter['Product'].unique()
)

bottleSize = st.sidebar.selectbox(
    'The product should be packaged in bottles of ... Liters',
    costPerLiter['Unit Conditionning'].unique()
)

conditionning = st.sidebar.selectbox(
    'The bottles will arrive packed in: ',
    ['VK 10 Kartons', 'VK 1/2 Palette', 'VK 1 Palette', 'VK 5 Paletten', 'VK 10 Paletten']
)

quantity = st.sidebar.text_area(
    'How many palettes/boxes do you want?'
)

addRequest = st.sidebar.button('Add to the request')


if addRequest:
    productRequested = Item(product, bottleSize, conditionning)
    customer = Customer(customerType, customerPotential)
    request = Request(int(quantity), productRequested, customer)

    minPrice = request.unitPrices[0] * request.nbBottles
    maxPrice = request.unitPrices[1] * request.nbBottles
    minUnitPrice = minPrice / request.nbBottles
    discountMinPrice = round(abs(float(minUnitPrice) - float(productRequested.standardPrices[1])) / float(productRequested.standardPrices[1]) * 100, 1)
    maxUnitPrice = maxPrice / request.nbBottles
    discountMaxPrice = round(abs(float(maxUnitPrice) - float(productRequested.standardPrices[1])) / float(productRequested.standardPrices[1]) * 100, 1)

    st.write('The request is composed of ' + str(int(request.nbBottles)) + ' bottles.')
    st.write('The minimum advised price for the request is: ' + str(float(minPrice)) + '€.')
    st.write('It represents a unit price of: ' + str(round(float(minUnitPrice), 2)) + '€, with a profit margin of ' + str(float(request.margins[0])*100) + '%.')
    st.write('Compared to the standard unit price of ' + str(float(productRequested.standardPrices[1])) + '€, it represents a discount of ' + str(discountMinPrice) + '%.')

    st.write('The maximum advised price for the request is: ' + str(round(float(maxPrice), 2)) + '€.')
    st.write('It represents a unit price of: ' + str(round(float(maxUnitPrice), 2)) + '€, with a profit margin of ' + str(float(request.margins[1])*100) + '%.')
    st.write('Compared to the standard unit price of ' + str(float(productRequested.standardPrices[1])) + '€, it represents a discount of ' + str(discountMaxPrice) + '%.')








