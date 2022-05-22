FROM auth

ENV HOME=/code_test
WORKDIR $HOME

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./ .
COPY ./entrypoint.sh /usr/local/bin

USER web

ENTRYPOINT ["entrypoint.sh"]
