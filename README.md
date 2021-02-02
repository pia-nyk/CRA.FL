# CRA.FL
Credit Risk Assessment using Federated Learning

<b> Motivation </b> <br/>
The lending institutions are at a constant risk from defaulting customers. Although, various subjective and quantitative factors are used to assess credit risks including AI models, the reliability of the assessment would increase multifold by using aggregated data from financial institutions. In order to mitigate the risk of breach of sensitive data in this case, we have developed a POC of credit risk assessment model that uses data from various financial institutions, without the need for centralisation of data. The accuracy of this model is comparable to the model trained with aggregated data (assuming same hyperparameters).

<br/><br/>
<b> Proposed System Architecture </b> <br/>
The system consists of a central authority server like RBI. The other participating clients simulate financial institutions disbursing loans. Scope of projects requires all systems to be connected to the same network. Multithread connection ensures connection between servers and clients remain intact even during the federated learning process. <br/>
<img src="https://github.com/pia-nyk/credit-risk-assessment-fl/extra_materials/blob/master/system_design.jpg" width="600" height="1000">

<br/><br/>
<b> Data </b><br/>
The loan data used has been retrieved from Kaggle, collected from 2007-2015. It includes current loan status and latest payment info. The target variable is a boolean whether the customer defaulted or not within specified time period. <br/>
Data consists of approx 1270000 data items and 20 features. To simulate data on financial institutions (which is generally non i.i.d), we divided the dat into 3 parts randomly for the 3 client instances. 10% of original data is used as test data on server. <br/>
The features include purpose of loan, interest rate, installments, debt to income ratio, revolving balance, revolving utility, inquiries in last 12 mnths, delinquency last 2 yrs, public records, employment length, home ownership, months since last deliquency, term, chargeoff, loan amnt, open accounts, total accounts. 


<br/><br/>
<b> Results </b><br/>
After each iteration, model at server was tested on testing data. The accuracy fluctuates a lot but eventually shows upward trend.<br/><br/>
<img src="https://github.com/pia-nyk/credit-risk-assessment-fl/extra_materials/blob/master/results.jpg" width="600" height="500">

<table>
  <tr> 
    <th> Training Method </th>
    <th> Accuracy </th>
  </tr>
  <tr>
    <td> Independent ML </td>
    <td> 72.4 </td>
  </tr>
  <tr>
    <td> Centralized ML </td>
    <td> 79.34 </td>
  </tr>
  <tr>
    <td> FL without Differential privacy </td>
    <td> 78.52 </td>
  </tr>
  <tr>
    <td> with Differential privacy </td>
    <td> 78.29 </td>
  </tr>
</table>
