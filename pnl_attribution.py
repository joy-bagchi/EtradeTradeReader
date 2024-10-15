#import libraries
import matplotlib.pyplot as plt
plt.style.use('ggplot')
from european_option import EuropeanOptionBS

# Then we enter the parameters, we give one example of set of parameters here.

#parameters 
S0 = 569.23 # stock price
K = 530 # strike price
r = .05 # risk-free interest rate
q = .0 # dividend
T0 = 1 # time to maturity
sigma0 = .184 # implied volatility BS
Type = "Call" # type of option
dt = 1 / 252 # 1 business day

# Market changes between t and t + dt
dS =  -2.73#-S0 * .1866 * dt**.5 # realised vol = .6
dsigma = .1
T1 = T0 - dt
S1 = S0 + dS
sigma1 = sigma0 + dsigma

# We calculate the P&L between t and t + δt

P0 = EuropeanOptionBS(S0, K, T0, r, q, sigma0, Type).price
P1 = EuropeanOptionBS(S1, K, T1, r, q, sigma1, Type).price
delta0 = EuropeanOptionBS(S0, K, T0, r, q, sigma0, Type).delta
isDeltaHedged = 1 #1 if is delta-hedged, 0 otherwise
dPandL = P1 - P0 - delta0 * dS * isDeltaHedged
print("P&L: " + str(dPandL))

# We decompose the P&L between the contribution of the different Greeks and we plot it with a barchart.

#initial greeks
theta0 = EuropeanOptionBS(S0, K, T0, r, q, sigma0, Type).theta
vega0 = EuropeanOptionBS(S0, K, T0, r, q, sigma0, Type).vega
gamma0 = EuropeanOptionBS(S0, K, T0, r, q, sigma0, Type).gamma
volga0 = EuropeanOptionBS(S0, K, T0, r, q, sigma0, Type).volga
vanna0 = EuropeanOptionBS(S0, K, T0, r, q, sigma0, Type).vanna

#P&L attribution
delta_PandL = delta0 * dS * (1 - isDeltaHedged)
theta_PandL = theta0 * dt
vega_PandL = vega0 * dsigma
gamma_PandL = 1 / 2 * gamma0 * dS**2
volga_PandL = 1 / 2 * volga0 * dsigma**2
vanna_PandL = vanna0 * dS * dsigma
unexplained = dPandL - sum([delta_PandL, theta_PandL, vega_PandL, gamma_PandL, volga_PandL, vanna_PandL])

y = [delta_PandL, theta_PandL, vega_PandL, gamma_PandL, volga_PandL, vanna_PandL, unexplained]
x = ["delta", "theta", "vega", "gamma", "volga", "vanna","unexplained"]

fig = plt.figure(figsize=(15, 5))
plt.bar(x, y)
plt.title("P&L Decomposition")
plt.show();