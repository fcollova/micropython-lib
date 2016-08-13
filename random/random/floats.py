from math import  log as _log, exp as _exp, pi as _pi, e as _e, ceil as _ceil
from math import sqrt as _sqrt, acos as _acos, cos as _cos, sin as _sin

NV_MAGICCONST = 4 * _exp(-0.5)/_sqrt(2.0)
TWOPI = 2.0*_pi
LOG4 = _log(4.0)
SG_MAGICCONST = 1.0 + _log(4.5)

## -------------------- triangular --------------------

def triangular(self, low=0.0, high=1.0, mode=None):
    """Triangular distribution.

    Continuous distribution bounded by given lower and upper limits,
    and having a given mode value in-between.

    http://en.wikipedia.org/wiki/Triangular_distribution

    """
    u = self.random()
    c = 0.5 if mode is None else (mode - low) / (high - low)
    if u > c:
        u = 1.0 - u
        c = 1.0 - c
        low, high = high, low
    return low + (high - low) * (u * c) ** 0.5

## -------------------- normal distribution --------------------

def normalvariate(self, mu, sigma):
    """Normal distribution.

    mu is the mean, and sigma is the standard deviation.

    """
    # mu = mean, sigma = standard deviation

    # Uses Kinderman and Monahan method. Reference: Kinderman,
    # A.J. and Monahan, J.F., "Computer generation of random
    # variables using the ratio of uniform deviates", ACM Trans
    # Math Software, 3, (1977), pp257-260.

    random = self.random
    while 1:
        u1 = random()
        u2 = 1.0 - random()
        z = NV_MAGICCONST*(u1-0.5)/u2
        zz = z*z/4.0
        if zz <= -_log(u2):
            break
    return mu + z*sigma

## -------------------- lognormal distribution --------------------

def lognormvariate(self, mu, sigma):
    """Log normal distribution.

    If you take the natural logarithm of this distribution, you'll get a
    normal distribution with mean mu and standard deviation sigma.
    mu can have any value, and sigma must be greater than zero.

    """
    return _exp(self.normalvariate(mu, sigma))

## -------------------- exponential distribution --------------------

def expovariate(self, lambd):
    """Exponential distribution.

    lambd is 1.0 divided by the desired mean.  It should be
    nonzero.  (The parameter would be called "lambda", but that is
    a reserved word in Python.)  Returned values range from 0 to
    positive infinity if lambd is positive, and from negative
    infinity to 0 if lambd is negative.

    """
    # lambd: rate lambd = 1/mean
    # ('lambda' is a Python reserved word)

    random = self.random
    u = random()
    while u <= 1e-7:
        u = random()
    return -_log(u)/lambd

## -------------------- von Mises distribution --------------------

def vonmisesvariate(self, mu, kappa):
    """Circular data distribution.

    mu is the mean angle, expressed in radians between 0 and 2*pi, and
    kappa is the concentration parameter, which must be greater than or
    equal to zero.  If kappa is equal to zero, this distribution reduces
    to a uniform random angle over the range 0 to 2*pi.

    """
    # mu:    mean angle (in radians between 0 and 2*pi)
    # kappa: concentration parameter kappa (>= 0)
    # if kappa = 0 generate uniform random angle

    # Based upon an algorithm published in: Fisher, N.I.,
    # "Statistical Analysis of Circular Data", Cambridge
    # University Press, 1993.

    # Thanks to Magnus Kessler for a correction to the
    # implementation of step 4.

    random = self.random
    if kappa <= 1e-6:
        return TWOPI * random()

    a = 1.0 + _sqrt(1.0 + 4.0 * kappa * kappa)
    b = (a - _sqrt(2.0 * a))/(2.0 * kappa)
    r = (1.0 + b * b)/(2.0 * b)

    while 1:
        u1 = random()

        z = _cos(_pi * u1)
        f = (1.0 + r * z)/(r + z)
        c = kappa * (r - f)

        u2 = random()

        if u2 < c * (2.0 - c) or u2 <= c * _exp(1.0 - c):
            break

    u3 = random()
    if u3 > 0.5:
        theta = (mu % TWOPI) + _acos(f)
    else:
        theta = (mu % TWOPI) - _acos(f)

    return theta

## -------------------- gamma distribution --------------------

def gammavariate(self, alpha, beta):
    """Gamma distribution.  Not the gamma function!

    Conditions on the parameters are alpha > 0 and beta > 0.

    """

    # alpha > 0, beta > 0, mean is alpha*beta, variance is alpha*beta**2

    # Warning: a few older sources define the gamma distribution in terms
    # of alpha > -1.0
    if alpha <= 0.0 or beta <= 0.0:
        raise ValueError('gammavariate: alpha and beta must be > 0.0')

    random = self.random
    if alpha > 1.0:

        # Uses R.C.H. Cheng, "The generation of Gamma
        # variables with non-integral shape parameters",
        # Applied Statistics, (1977), 26, No. 1, p71-74

        ainv = _sqrt(2.0 * alpha - 1.0)
        bbb = alpha - LOG4
        ccc = alpha + ainv

        while 1:
            u1 = random()
            if not 1e-7 < u1 < .9999999:
                continue
            u2 = 1.0 - random()
            v = _log(u1/(1.0-u1))/ainv
            x = alpha*_exp(v)
            z = u1*u1*u2
            r = bbb+ccc*v-x
            if r + SG_MAGICCONST - 4.5*z >= 0.0 or r >= _log(z):
                return x * beta

    elif alpha == 1.0:
        # expovariate(1)
        u = random()
        while u <= 1e-7:
            u = random()
        return -_log(u) * beta

    else:   # alpha is between 0 and 1 (exclusive)

        # Uses ALGORITHM GS of Statistical Computing - Kennedy & Gentle

        while 1:
            u = random()
            b = (_e + alpha)/_e
            p = b*u
            if p <= 1.0:
                x = p ** (1.0/alpha)
            else:
                x = -_log((b-p)/alpha)
            u1 = random()
            if p > 1.0:
                if u1 <= x ** (alpha - 1.0):
                    break
            elif u1 <= _exp(-x):
                break
        return x * beta

## -------------------- Gauss (faster alternative) --------------------

def gauss(self, mu, sigma):
    """Gaussian distribution.

    mu is the mean, and sigma is the standard deviation.  This is
    slightly faster than the normalvariate() function.

    Not thread-safe without a lock around calls.

    """

    # When x and y are two variables from [0, 1), uniformly
    # distributed, then
    #
    #    cos(2*pi*x)*sqrt(-2*log(1-y))
    #    sin(2*pi*x)*sqrt(-2*log(1-y))
    #
    # are two *independent* variables with normal distribution
    # (mu = 0, sigma = 1).
    # (Lambert Meertens)
    # (corrected version; bug discovered by Mike Miller, fixed by LM)

    # Multithreading note: When two threads call this function
    # simultaneously, it is possible that they will receive the
    # same return value.  The window is very small though.  To
    # avoid this, you have to use a lock around all calls.  (I
    # didn't want to slow this down in the serial case by using a
    # lock here.)

    random = self.random
    z = self.gauss_next
    self.gauss_next = None
    if z is None:
        x2pi = random() * TWOPI
        g2rad = _sqrt(-2.0 * _log(1.0 - random()))
        z = _cos(x2pi) * g2rad
        self.gauss_next = _sin(x2pi) * g2rad

    return mu + z*sigma

## -------------------- beta --------------------
## See
## http://sourceforge.net/bugs/?func=detailbug&bug_id=130030&group_id=5470
## for Ivan Frohne's insightful analysis of why the original implementation:
##
##    def betavariate(self, alpha, beta):
##        # Discrete Event Simulation in C, pp 87-88.
##
##        y = self.expovariate(alpha)
##        z = self.expovariate(1.0/beta)
##        return z/(y+z)
##
## was dead wrong, and how it probably got that way.

def betavariate(self, alpha, beta):
    """Beta distribution.

    Conditions on the parameters are alpha > 0 and beta > 0.
    Returned values range between 0 and 1.

    """

    # This version due to Janne Sinkkonen, and matches all the std
    # texts (e.g., Knuth Vol 2 Ed 3 pg 134 "the beta distribution").
    y = self.gammavariate(alpha, 1.)
    if y == 0:
        return 0.0
    else:
        return y / (y + self.gammavariate(beta, 1.))

## -------------------- Pareto --------------------

def paretovariate(self, alpha):
    """Pareto distribution.  alpha is the shape parameter."""
    # Jain, pg. 495

    u = 1.0 - self.random()
    return 1.0 / u ** (1.0/alpha)

## -------------------- Weibull --------------------

def weibullvariate(self, alpha, beta):
    """Weibull distribution.

    alpha is the scale parameter and beta is the shape parameter.

    """
    # Jain, pg. 499; bug fix courtesy Bill Arms

    u = 1.0 - self.random()
    return alpha * (-_log(u)) ** (1.0/beta)

