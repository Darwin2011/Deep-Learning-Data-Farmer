#!usr/bin/env python

class Result_Builder():

    def __init__(self):
        pass

    def buildResultTable(self, content):
        HEADER = """
        <html>
            <table border=0 cellspacing=0 cellpadding=0  style='margin-left:-.4pt;border-collapse:collapse'>
        """
        FOOTER = """
            </table>
        </html>
        """
        return HEADER + content + FOOTER

    def buildHeader(self, header):
        is_first = True
        header_html = "<tr style='height:15.75pt'>"
        for item in header:
            if is_first:
                is_first = False
                header_html += "<td nowrap style='border:solid windowtext 1.0pt;border-bottom:none;background:#2F75B5;padding:0in 5.4pt 0in 5.4pt;height:15.75pt'><p><span style='color:white'>%s</span></p></td>" % item
            else:
                header_html += "<td nowrap style='border-top:solid windowtext 1.0pt;border-left:none;border-bottom:none;border-right:solid windowtext 1.0pt;background:#2F75B5;padding:0in 5.4pt 0in 5.4pt;height:15.75pt'><p><span style='color:white'>%s</span></p></td>" % item

        header_html += "</tr>"
        return header_html

    def builderItems(self, header, dictItems, length):
        is_first = True
        items_html = ""
        item_html = ""
        for index in range(length):
            item_html = "<tr style='height:15.0pt'>"
            is_first = True
            for item in header:
                if is_first:
                    is_first = False
                    item_html += "<td nowrap style='border:solid windowtext 1.0pt;padding:0in 5.4pt 0in 5.4pt;height:15.0pt'><p><span style='color:black'>%s</span></p></td>" % dictItems[item][index]
                else:
                    item_html += "<td nowrap style='border:solid windowtext 1.0pt;border-left:none;padding:0in 5.4pt 0in 5.4pt;height:15.0pt'><p><span style='color:black'>%s</span></p></td>" % dictItems[item][index]
            item_html +="</tr>"
            items_html += item_html
        return items_html


    def buildZipLog(self, log_path):
        pass

    def buildImg(self, image):
        pass

if __name__ == "__main__":
    builder = Result_Builder()
    header = ("a", "b", "c")
    length = 3
    dictItems = {"a" : [1,2,3], "b":[2,3,4], "c":[3,4,5]}
    headerhtml = builder.buildHeader(header)
    bodyhtml = builder.builderItems(header, dictItems, length)
    print builder.buildResultTable(headerhtml + bodyhtml)
