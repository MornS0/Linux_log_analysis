from django import template

register = template.Library()

@register.filter    #这里可以加参数，默认name为该函数名称
def rep(val, val2):
    try:
        if val == "None":
            return str(val2)
        else:
            return str(val)
    except:
        return ""