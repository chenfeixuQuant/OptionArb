from __future__ import division
import pandas as pd
import numpy as np
from datetime import datetime 
from datetime import timedelta
import os

def Calcuate_performance_indicators(return_data, period, type_s):
    #总收益
    Total_return=(return_data+1).cumprod(axis=0)[-1]-1
    #平均日收益
    Average_return = return_data.mean()

    #年化收益
    Annualized_Return = (return_data+1).cumprod(axis=0)[-1]**(365/len(return_data))-1
    #年化波动率：如果用月收益,年化应该乘以12的平方根
    Annualized_Volatility = return_data.std(axis=0)*period**0.5
    #年化夏普比
    Sharp = Annualized_Return/Annualized_Volatility
    #年化sortino比率
    down_return_data = []
    for r in return_data:
        if r < 0:
            down_return_data.append(r)
    Annualized_Down_Volatility = np.array(down_return_data).std(axis=0)*period**0.5
    Sortino = Annualized_Return/Annualized_Down_Volatility
    #最大回撤
    Maxdrawndown=[]
    l=[]
    for j in range(len(return_data)):
        l.append(((return_data+1).cumprod(axis=0)[j]-(return_data+1).cumprod(axis=0)[:j].max())/(return_data+1).cumprod(axis=0)[:j].max())
    Maxdrawndown.append(np.nanmin(np.array(l)));

    indis = [Total_return,Average_return,Annualized_Return,Annualized_Volatility,Sharp,Maxdrawndown[0],Sortino]

    df = pd.DataFrame(index = [type_s], columns=['TotalReturn','AverageReturn','AnnualizedReturn',\
                      'AnnualizedVol','Sharpe','MaxDrawdown','Sortino','Calmar','WinRate','P/L Ratio','MaxProfit','MaxLoss'])
    df['TotalReturn']=indis[0]
    df['AverageReturn']=indis[1]
    df['AnnualizedReturn']=indis[2]
    df['AnnualizedVol']=indis[3]
    df['Sharpe']=indis[4]
    df['MaxDrawdown']=indis[5]
    df['Sortino']=indis[6]
    
    df["Calmar"] =  -df['AnnualizedReturn']/df['MaxDrawdown']
    df["WinRate"] = sum(np.where(return_data > 0, 1, 0)) /sum(np.where(return_data == 0, 0, 1))
    df["P/L Ratio"] = -np.nanmean(return_data[return_data>0])/np.nanmean(return_data[return_data<0])
    df["MaxProfit"] = return_data.max()
    df["MaxLoss"] = return_data.min()
   
    return(df)

#%%
def arbitrage(begin, end, number, option_info, fund):
	
#    PnL = []
#    Long_PnL = []
#    Short_PnL = []
    Return = []
    Long_Return = []
    Short_Return = []
#    PnL_cum_fees = []
    Period = []
    fund_cum = []
    long_fund_cum = []
    short_fund_cum = []
    
    Long_fund = fund
    Short_fund = fund
    #skip expiry dates
    special_list = ['2018-04-27', '2018-05-30', '2018-06-28', '2018-07-30']

    while begin != end:

        if begin not in special_list:
#%%
            call_data = pd.read_csv('../option_data/option_' + begin + '.csv')
            put_data = pd.read_csv('../option_data/option_' + begin + '.csv')
            
            data = call_data.append(put_data, ignore_index=True)
            
            portfolio = {}
            
            longs = [] 
            shorts = []
            long_strikes = []
            short_strikes = []
            long_settles = []
            short_settles = []
            long_types = []
            short_types = []
            
            settle_c = np.array(call_data['Settle(C)'].tolist())
            t_p_c =  np.array(call_data['T-Price(tree,C)'].tolist())
            
            settle_p = np.array(put_data['Settle(P)'].tolist())
            t_p_p =  np.array(put_data['T-Price(tree,P)'].tolist())
            
            #t_p_c =  np.array(data['T-Price(BS,C)'].tolist())
            diff_c = settle_c - t_p_c
            diff_p = settle_p - t_p_p
            
            diff= np.append(diff_c, diff_p)
            
            border = len(diff)/2
                      
            sort_index = np.argsort(diff).tolist()
            l=0
            s=0
            
            #3sigma去极值
#            mu = np.mean(diff)
#            sigma = np.std(diff)
#            up = mu + 3*sigma
#            down = mu - 3*sigma

            #分位数去极值
            up = pd.DataFrame(diff).quantile([0.01,0.99]).iloc[1,:].tolist()[0]
            down = pd.DataFrame(diff).quantile([0.01,0.99]).iloc[0,:].tolist()[0]
            
            for k in range(len(sort_index)):
                if diff[sort_index[k]]>= down:
                    l = k
                    break
                
            for k in range(len(sort_index)):
                if diff[sort_index[k]]<= up:
                    s = k
                
            s = len(sort_index) - s - 1
            #print(s)
            #print(l)
            
            long_index = sort_index[l:number+l]
            if s == 0:
                short_index = sort_index[-number-s:]
            else:
                short_index = sort_index[-number-s:-s]
            #print(short_index)
            #print(long_index)
            
            for i in range(number):
                if long_index[i] < border:
                    longs.append(data.loc[long_index[i],'Option Code'])
                    #print(long_index[i])
                    long_strikes.append(float(data.loc[long_index[i],'Strike']))
                    long_settles.append(float(data.loc[long_index[i],'Settle(C)']))
                    long_types.append('C')
                else:
                    longs.append(data.loc[long_index[i],'Option Code'])
                    #print(longs[0])
                    long_strikes.append(float(data.loc[long_index[i],'Strike']))
                    long_settles.append(float(data.loc[long_index[i],'Settle(P)']))
                    long_types.append('P')
                
                if short_index[i] < border:
                    shorts.append(data.loc[short_index[i],'Option Code'])
                    short_strikes.append(float(data.loc[short_index[i],'Strike']))
                    short_settles.append(float(data.loc[short_index[i],'Settle(C)']))
                    short_types.append('C')
                else:
                    shorts.append(data.loc[short_index[i],'Option Code'])
                    short_strikes.append(float(data.loc[short_index[i],'Strike']))
                    short_settles.append(float(data.loc[short_index[i],'Settle(P)']))
                    short_types.append('P')
                
            portfolio['1'] = [longs, long_types, long_strikes, long_settles]
            portfolio['-1'] = [shorts, short_types, short_strikes, short_settles]
             
#%% arb
            current_date = datetime.strptime(begin,'%Y-%m-%d')
            count = 1
            next_date = str(current_date + timedelta(days = count))
            while((not os.path.exists('../option_data/arb_data_'+ next_date[0:10] + '.csv')) and next_date[0:10]<='2018-10-01'):
                count = count + 1
                next_date = str(current_date + timedelta(days = count))
            
            arb_data = pd.read_csv('../option_data/arb_data_' + next_date[0:10] + '.csv')
            
            long_fund = 0
            short_fund = 0
            long_pnl = 0 
            short_pnl = 0
            pnl = 0
            
            long_fee = 0
            short_fee = 0

            for i in range(number):
                
                print(next_date[0:10]+':'+str(i)+':') 
                
                long_i = arb_data[(arb_data['Option Code'] == portfolio['1'][0][i])].index.tolist()[0]   			 
                short_i = arb_data[(arb_data['Option Code'] == portfolio['-1'][0][i])].index.tolist()[0]
                
                if portfolio['1'][1][i] == 'C' and portfolio['-1'][1][i] == 'C':
                    long_settle, long_open = arb_data.loc[long_i,'Settle(C)'],arb_data.loc[long_i,'Open(C)']
                    short_settle, short_open = arb_data.loc[short_i,'Settle(C)'],arb_data.loc[short_i,'Open(C)']
                    
                elif portfolio['1'][1][i] == 'C' and portfolio['-1'][1][i] == 'P':
                    long_settle, long_open = arb_data.loc[long_i,'Settle(C)'],arb_data.loc[long_i,'Open(C)']
                    short_settle, short_open = arb_data.loc[short_i,'Settle(P)'],arb_data.loc[short_i,'Open(P)']
                    
                elif portfolio['1'][1][i] == 'P' and portfolio['-1'][1][i] == 'C':
                    long_settle, long_open = arb_data.loc[long_i,'Settle(P)'],arb_data.loc[long_i,'Open(P)']
                    short_settle, short_open = arb_data.loc[short_i,'Settle(C)'],arb_data.loc[short_i,'Open(C)']
                    
                elif portfolio['1'][1][i] == 'P' and portfolio['-1'][1][i] == 'P':
                    long_settle, long_open = arb_data.loc[long_i,'Settle(P)'],arb_data.loc[long_i,'Open(P)']
                    short_settle, short_open = arb_data.loc[short_i,'Settle(P)'],arb_data.loc[short_i,'Open(P)']
                    
                print(portfolio['1'][0][i] + ',s:' + str(long_settle)+ ',o:'+str(long_open))
                print(portfolio['-1'][0][i] + ',s:' + str(short_settle) + ',o:' + str(short_open))
                
                long_info = option_info[(option_info['Option Code'] == portfolio['1'][0][i])].index.tolist()[0]   			 
                short_info = option_info[(option_info['Option Code'] == portfolio['-1'][0][i])].index.tolist()[0]
                 
                #buy side
                if long_open > 0 and long_settle > 0:
                    if option_info.loc[long_info,'Tier']==1:
                        long_fee = 3
                    elif option_info.loc[long_info,'Tier']==2:
                        long_fee = 1
                    elif option_info.loc[long_info,'Tier']==3:
                        long_fee = 0.5
                        
                    long_fund = long_fund + long_open*option_info.loc[long_info,'Contract Size'] + long_fee
                    long_pnl = long_pnl + (long_settle - long_open)*option_info.loc[long_info,'Contract Size'] - 2*long_fee
                
                #short side
                if short_open > 0 and short_settle > 0:
                    if option_info.loc[short_info,'Tier']==1:
                        short_fee = 3
                    elif option_info.loc[short_info,'Tier']==2:
                        short_fee = 1
                    elif option_info.loc[short_info,'Tier']==3:
                        short_fee = 0.5
                        
                    short_fund = short_fund + short_open*option_info.loc[short_info,'Contract Size'] + short_fee
                    short_pnl = short_pnl - (short_settle - short_open)*option_info.loc[short_info,'Contract Size'] - 2*short_fee
                
                if short_fund>0:
                    print('short size:'+str(option_info.loc[short_info,'Contract Size']))
                    print('short fund:'+str(short_fund))
                if long_fund>0:
                    print('long size:'+str(option_info.loc[long_info,'Contract Size']))
                    print('long fund:'+str(long_fund))
                #print('pnl:'+str(long_pnl+short_pnl))

#%% long-short
            if long_fund > 0 and short_fund > 0:
                #hands_portfolio_long =  int(l_fund/long_fund)
                #hands_portfolio_short = int(s_fund/short_fund)
                #pnl = long_pnl*hands_portfolio_long +short_pnl*hands_portfolio_short
                pnl = long_pnl+short_pnl
                #print('long hands:'+str(hands_portfolio_long))
                #print('short hands:'+str(hands_portfolio_short))
                print('pnl:'+str(pnl))
                
            elif long_fund == 0 and short_fund > 0:
                #hands_portfolio_short = int(s_fund/short_fund)
                #pnl = short_pnl*hands_portfolio_short
                pnl = short_pnl
                #print('short hands:'+str(hands_portfolio_short))
                print('pnl:'+str(pnl))
                
            elif short_fund == 0 and long_fund > 0:
                #hands_portfolio_long = int(l_fund/long_fund)
                #pnl = long_pnl*hands_portfolio_long
                pnl = long_pnl
                #print('long hands:'+str(hands_portfolio_long))
                print('pnl:'+str(pnl))
            
            print('---------------------------------')    
            
            Return.append(pnl/fund)
            fund = fund + pnl
            fund_cum.append(round(fund,2))
            
#%% long
            if long_fund > 0:
 
                Long_Return.append(long_pnl/Long_fund)
                Long_fund = Long_fund + long_pnl
                long_fund_cum.append(round(Long_fund,2))
            else:
                Long_Return.append(0)
                long_fund_cum.append(round(Long_fund,2))
#%% short
            if short_fund > 0:
 
                Short_Return.append(short_pnl/Short_fund)
                Short_fund = Short_fund + short_pnl
                short_fund_cum.append(round(Short_fund,2))
            else:
                Short_Return.append(0)
                short_fund_cum.append(round(Short_fund,2))
                
            Period.append(next_date[0:10])
            begin = next_date[0:10]
            
        else:
            count = 1
            current_date = datetime.strptime(begin,'%Y-%m-%d')
            next_date = str(current_date + timedelta(days = count))
            while((not os.path.exists('../option_data/option_'+ next_date[0:10] + '.csv')) and next_date[0:10]<='2018-10-01'):
                count = count + 1
                next_date = str(current_date + timedelta(days = count))
            begin = next_date[0:10]

    return Period,fund_cum,Return,long_fund_cum,Long_Return,short_fund_cum,Short_Return


option_info=pd.read_excel('../option_info.xlsx') 

begin = '2018-05-02'
end = '2018-07-31'

fund = 100000

Period,fund_cum,Return,long_fund_cum,Long_Return,short_fund_cum,Short_Return = arbitrage(begin, end, 5, option_info, fund)


data = pd.DataFrame(index = Period, columns=['FundCum','Return','LongFundCum','LongReturn','ShortFundCum','ShortReturn'])
data['FundCum']=np.array(fund_cum)
data['Return']=np.array(Return)
data['LongFundCum']=np.array(long_fund_cum)
data['LongReturn']=np.array(Long_Return)
data['ShortFundCum']=np.array(short_fund_cum)
data['ShortReturn']=np.array(Short_Return)

indicators = Calcuate_performance_indicators(data['Return'], 252, 'Long-Short')
indicators_long = Calcuate_performance_indicators(data['LongReturn'], 252, 'Long')
indicators_short = Calcuate_performance_indicators(data['ShortReturn'], 252, 'Short')

indis = (indicators.append(indicators_long)).append(indicators_short)

print(indicators.T)

name='Results(5,BinomialTree)'
wbw = pd.ExcelWriter(name+'.xlsx')
data.to_excel(wbw, 'PnL')
indis.to_excel(wbw, 'Indicators')

    
wbw.save()
wbw.close()









